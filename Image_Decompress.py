import numpy as np
import matplotlib.pyplot as plt
import cv2 as cv
import json
import struct

#Find the closest Power of Two
def PowerOfTwo(x):
  return 1 << (x - 1).bit_length()

#inverses the bit-reversal permutation
def bit_reverse_indices(N):
  bits = int(np.log2(N))
  return np.array([int(f'{i:0{bits}b}'[::-1], 2) for i in range(N)])

#Basic IFFT
def Inverse_FFT(signal):
  N = len(signal)

  if not (N & (N - 1) == 0) and N != 0:
    New_N = PowerOfTwo(N)
    New_Signal = np.zeros(New_N, dtype=complex)
    New_Signal[:N] = signal
    signal = New_Signal
    N = New_N

  New_Signal = np.array(signal, dtype=complex)
  indices = bit_reverse_indices(N)
  New_Signal = New_Signal[indices]

  stages = int(np.log2(N))
  for stage in range(1, stages + 1):
    step = 2 ** stage
    half_step = step // 2
    twiddle_factors = np.exp(2j * np.pi * np.arange(half_step) / step)

    for k in range(0, N, step):
      for n in range(half_step):
        a = New_Signal[k + n]
        b = twiddle_factors[n] * New_Signal[k + n + half_step]
        New_Signal[k + n] = a + b
        New_Signal[k + n + half_step] = a - b

  return New_Signal / N

#IFFT for two dims
def Inverse_TwoDFFT(spectrum):
  IFFT_Rows = np.array([Inverse_FFT(row) for row in spectrum])
  IFFT_Cols = np.array([Inverse_FFT(col) for col in IFFT_Rows.T]).T
  return IFFT_Cols

#Removes the zeroes that could be added during compression 
def Remove_Padding(image):
  row_mask = ~np.all(image == 0, axis=1)
  col_mask = ~np.all(image == 0, axis=0)

  return image[row_mask][:, col_mask]

#Rebuilds the Huffman decoder
def rebuild_huffman_decoder(codebook):
  decoder = {}
  for symbol, code in codebook.items():
    decoder[code] = symbol
  return decoder

#Getting the bitstream from bytes
def Bytes_to_Bits(byte_data, padding):
  bits = ''.join(f'{byte:08b}' for byte in byte_data)
  return bits[:-padding] if padding > 0 else bits

#Decode the bitstream using the Huffman decoder
def decode_bitstream(bitstream, padding, decoder):
  bitstream = Bytes_to_Bits(bitstream, padding)

  buffer = ''
  i = 0
  current_block = []
  all_blocks = []

  while i < len(bitstream):
    buffer += bitstream[i]
    i += 1

    if buffer in decoder:
      runcat = decoder[buffer]
      run, cat = runcat

      val_bits = bitstream[i:i+cat] if cat > 0 else ''
      i += cat
      current_block.append((runcat, val_bits))

      if runcat == (0, 0):
        all_blocks.append(current_block)
        current_block = []
      buffer = ''

  return all_blocks

#RLE DecCode
def rle_decode(rle_block):
  result = []
  for (run, cat), val_bits in rle_block:
    if (run, cat) == (0, 0):
      break

    result.extend([0] * run)
    if cat == 0:
      result.append(0)
      continue

    if val_bits[0] == '1':
      val = int(val_bits, 2)
    else:
      inverted = ''.join('1' if b == '0' else '0' for b in val_bits)
      val = -int(inverted, 2)
        
    result.append(val)
  while len(result) < 64:
    result.append(0)
    
  return result

#Determines the number of blocks
def zigzag_indices(n=8):
  indexorder = sorted(((x, y) for x in range(n) for y in range(n)),
                      key=lambda s: (s[0]+s[1], -s[1] if (s[0]+s[1]) % 2 else s[1]))
  return indexorder

#Dequintize the block with the given Matrix
def dequantize_block(block, quant_table):
  return block * quant_table

#Inverse zigzag
def inverse_zigzag(flat_block, indices):
  block = np.zeros((8,8), dtype=np.float32)
  for idx, (i, j) in enumerate(indices):
    block[i, j] = flat_block[idx]
  return block

#reconstruction from blocks
def reconstruct_image(blocks, shape, block_size=8):
  h, w = shape
  image = np.zeros((h, w), dtype=np.float32)
  idx = 0
  for i in range(0, h, block_size):
    for j in range(0, w, block_size):
      image[i:i+block_size, j:j+block_size] = blocks[idx]
      idx += 1
  return image

#Chroma upsampling 4:2:0
def chroma_upsample_420(Cr, Cb, target_shape):
  h, w = target_shape
  Cr_up = cv.resize(Cr, (w, h), interpolation=cv.INTER_LINEAR)
  Cb_up = cv.resize(Cb, (w, h), interpolation=cv.INTER_LINEAR)
  return Cr_up, Cb_up

#Block reconstruction
def reconstruct_blocks(rle_blocks):
  decoded_blocks = [rle_decode(block) for block in rle_blocks]
  indices = sorted(((x, y) for x in range(8) for y in range(8)),
        key=lambda s: (s[0]+s[1], -s[1] if (s[0]+s[1]) % 2 else s[1]))
  return [inverse_zigzag(flat, indices) for flat in decoded_blocks]

#Gets the number of blocks in the given shape
def get_block_count(shape, block_size=8):
  h, w = shape
  pad_h = (block_size - (h % block_size)) % block_size
  pad_w = (block_size - (w % block_size)) % block_size
  padded_h = h + pad_h
  padded_w = w + pad_w
  return (padded_h // block_size) *(padded_w // block_size)

#Loads the compressed file and extracts the header and data
def load_compressed_file(filename):
  with open(filename, 'rb') as f:
    header_len_bytes = f.read(4)
    header_len = struct.unpack('>I', header_len_bytes)[0]

    header_bytes = f.read(header_len)
    header_json = header_bytes.decode('utf-8')
    header = json.loads(header_json)

    S_bytes = f.read()

  Y_shape = tuple(header["Y_shape"])
  Cr_shape = tuple(header["Cr_shape"])
  Cb_shape = tuple(header["Cb_shape"])
  padding = header["padding"]
  codes = {eval(k): v for k, v in header["huffman_codes"].items()}

  return S_bytes, padding, codes, Y_shape, Cr_shape, Cb_shape


Q_For_Y = np.array([
  [16, 11, 10, 16, 24, 40, 51, 61],
  [12, 12, 14, 19, 26, 58, 60, 55],
  [14, 13, 16, 24, 40, 57, 69, 56],
  [14, 17, 22, 29, 51, 87, 80, 62],
  [18, 22, 37, 56, 68, 109, 103, 77],
  [24, 35, 55, 64, 81, 104, 113, 92],
  [49, 64, 78, 87, 103, 121, 120, 101],
  [72, 92, 95, 98, 112, 100, 103, 99]
])

Q_For_Clr = np.array([
  [17, 18, 24, 47, 99, 99, 99, 99],
  [18, 21, 26, 66, 99, 99, 99, 99],
  [24, 26, 56, 99, 99, 99, 99, 99],
  [47, 66, 99, 99, 99, 99, 99, 99],
  [99, 99, 99, 99, 99, 99, 99, 99],
  [99, 99, 99, 99, 99, 99, 99, 99],
  [99, 99, 99, 99, 99, 99, 99, 99],
  [99, 99, 99, 99, 99, 99, 99, 99]
])

indices = zigzag_indices(n=8)
S_bytes, padding, codes, Y_shape, Cr_shape, Cb_shape = load_compressed_file('compressed_image.huff')
decoder = rebuild_huffman_decoder(codes)

indices = zigzag_indices(n=8)
rle_blocks = decode_bitstream(S_bytes, padding, decoder)

decoded_zigzags = [rle_decode(block) for block in rle_blocks]

Y_block_count = get_block_count(Y_shape)
Cr_block_count = get_block_count(Cr_shape)
Cb_block_count = get_block_count(Cb_shape)

Y_dec_zigzag = decoded_zigzags[:Y_block_count]
Cr_dec_zigzag = decoded_zigzags[Y_block_count:Y_block_count + Cr_block_count]
Cb_dec_zigzag = decoded_zigzags[Y_block_count + Cr_block_count:]

Y_dec_blocks = [dequantize_block(inverse_zigzag(block, indices), Q_For_Y) for block in Y_dec_zigzag]
Cr_dec_blocks = [dequantize_block(inverse_zigzag(block, indices), Q_For_Clr) for block in Cr_dec_zigzag]
Cb_dec_blocks = [dequantize_block(inverse_zigzag(block, indices), Q_For_Clr) for block in Cb_dec_zigzag]

Y_ifft_blocks = [Inverse_TwoDFFT(block).real for block in Y_dec_blocks]
Cr_ifft_blocks = [Inverse_TwoDFFT(block).real for block in Cr_dec_blocks]
Cb_ifft_blocks = [Inverse_TwoDFFT(block).real for block in Cb_dec_blocks]

Y_reconstructed = reconstruct_image(Y_ifft_blocks, Y_shape)
Cr_reconstructed = reconstruct_image(Cr_ifft_blocks, Cr_shape)
Cb_reconstructed = reconstruct_image(Cb_ifft_blocks, Cb_shape)

Y_reconstructed = np.clip(Y_reconstructed, 0, 255).astype(np.uint8)
Cr_reconstructed = np.clip(Cr_reconstructed, 0, 255).astype(np.uint8)
Cb_reconstructed = np.clip(Cb_reconstructed, 0, 255).astype(np.uint8)

Cr_reconstructed, Cb_reconstructed = chroma_upsample_420(Cr_reconstructed, Cb_reconstructed, Y_shape)

reconstructed_ycrcb = cv.merge([Y_reconstructed, Cr_reconstructed, Cb_reconstructed])
final_image = cv.cvtColor(reconstructed_ycrcb, cv.COLOR_YCrCb2BGR)

plt.figure(figsize=(12, 8))

plt.subplot(1, 2, 1)
plt.imshow(cv.cvtColor(final_image, cv.COLOR_BGR2RGB))
plt.title('Reconstructed Image')
plt.axis('off')

plt.subplot(1, 2, 2)
plt.imshow(Y_reconstructed, cmap='gray')
plt.title('Y Channel (Luminance)')
plt.axis('off')

plt.tight_layout()
plt.show()

cv.imwrite('reconstructed_image.jpg', final_image)
print("Reconstructed image saved as 'reconstructed_image.jpg'")


