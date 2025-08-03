import numpy as np
import cv2 as cv
import heapq
from collections import Counter
import json
import struct

EOB = (0, 0)
class Huffman_Node: 
  def __init__(self, Freq, Symbol = None, Left = None, Right = None):
    self.Freq = Freq
    self.symbol = Symbol
    self.Left = Left
    self.Right = Right
  def __lt__(self, other):
    return self.Freq < other.Freq

# Builds a Huffman tree from the given FFT data
def Build_Huffman_tree(symbols):
  freq = Counter(symbols)
  heap = [Huffman_Node(f, s) for s, f in freq.items()]
  heapq.heapify(heap)

  while len(heap) > 1:
    node1 = heapq.heappop(heap)
    node2 = heapq.heappop(heap)
    merged = Huffman_Node(node1.Freq + node2.Freq, Left=node1, Right=node2)
    heapq.heappush(heap, merged)

  return heap[0]

#Builds Huffman codes
def build_huffman_codes(tree):
  codes = {}
  def build_codes_helper(node, current_code):
    if node is None:
      return
    if node.symbol is not None:
      codes[node.symbol] = current_code
      return
    build_codes_helper(node.Left, current_code + "0")
    build_codes_helper(node.Right, current_code + "1")
  build_codes_helper(tree, "")
  return codes

#Encodes the data using the Huffman codes
def huffman_encode(data, codes):
  return ''.join(codes[sym] for sym in data)

#Converts a symbol to a string representation
def stringify_symbol(sym):
  return f"r:{sym[0]},v:{sym[1]}" if sym != EOB else "EOB"


#Finds the Next power of two 
def PowerOfTwo(x):
  return 1 << (x - 1).bit_length()

def bit_reverse_indices(N):
  bits = int(np.log2(N))
  return np.array([int(f'{i:0{bits}b}'[::-1], 2) for i in range(N)])

#My Custom Fast Fourier Transform that uses iterative algorithm and Bit reversal
#It Mimics the real way it is done in Jpeg compression
def FFT(signal):
  N = len(signal)

  if not(N & (N - 1) == 0) and N != 0:
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
    twiddle_factors = np.exp(-2j * np.pi * np.arange(half_step) / step)

    for k in range(0, N, step):
      for n in range(half_step):
        a = New_Signal[k + n]
        b = twiddle_factors[n] * New_Signal[k + n + half_step]
        New_Signal[k + n] = a + b
        New_Signal[k + n + half_step] = a - b
  return New_Signal


#Two Dimensiaonal applying of FFT
def TwoDFFT(image):
  FFT_Rows = np.array([FFT(row) for row in image])
  FFT_Cols = np.array([FFT(col) for col in FFT_Rows.T]).T
  return FFT_Cols


#Chroma Subsampling 4:2:0
def chroma_subsample_420(Cr, Cb):
  Cb_sub = Cb[::2,::2]
  Cr_sub = Cr[::2,::2]
  return Cr_sub, Cb_sub

#Converts a bitstring to bytes, adding padding if necessary
def  Bits_to_Bytes(bitstring):
  padding = (8 - len(bitstring) % 8) % 8
  bitstring += '0' * padding
  byte_arr = bytearray()
  for i in range(0, len(bitstring), 8):
    byte = int(bitstring[i:i+8], 2)
    byte_arr.append(byte)
  return bytes(byte_arr), padding

#Zigzag scan for 8x8 blocks
def zigzag_indices(n=8):
  indexorder = sorted(((x, y) for x in range(n) for y in range(n)),
                      key=lambda s: (s[0]+s[1], -s[1] if (s[0]+s[1]) % 2 else s[1]))
  return indexorder

#Extracts a zigzag scan from the given block
def zigzag_scan(block, indices):
  if np.iscomplexobj(block):
    return [block[i,j].real for (i, j) in indices]
  else:
    return [block[i,j] for (i, j) in indices]

#Divivdes the given channel into blox(8 for now) CHANGED
def divide_blocks(image, block_size=8):
  h, w = image.shape
  pad_h = (block_size - (h % block_size)) % block_size
  pad_w = (block_size - (w % block_size)) % block_size

  padded = np.pad(image, ((0, pad_h), (0, pad_w)), mode='constant', constant_values=0)
  blocks = []

  for i in range(0, padded.shape[0], block_size):
    for j in range(0, padded.shape[1], block_size):
      blocks.append(padded[i:i+block_size, j:j+block_size])
  return blocks

#Quantizes the block with the given Matrix and threshold
def quantize_block(block, quant_table, threshold=0):
  quantized = np.round(block.real / quant_table)
  quantized[np.abs(quantized) < threshold] = 0
  return quantized.astype(int)

#Value return for Huffman encoding
def value_category(val):
  if val == 0:
    return 0
  return int(abs(int(val))).bit_length()

#Encodes the data using Run Length Encoding CHANGED
def rle_encode(block):
  result = []
  zero_count = 0

  last_non_zero = -1
  for i in reversed(range(len(block))):
    if block[i] != 0:
      last_non_zero = i
      break

  if last_non_zero == -1:
    return [((0, 0), '')]
  for i in range(last_non_zero + 1):
    val = int(round(block[i]))
    if val == 0:
      zero_count += 1
    else:
      while zero_count > 15:
        result.append(((15, 0), ''))
        zero_count -= 16

      cat = value_category(val)
      val_bits = format(abs(val), f'0{cat}b')
      if val < 0:
        val_bits = ''.join('1' if b == '0' else '0' for b in val_bits)

      result.append(((zero_count, cat), val_bits))
      zero_count = 0

  result.append(((0, 0),''))
  return result


#File Saving
def save_compressed_file(filename, S_bytes, padding, codes, Y_shape, Cr_shape, Cb_shape):
  header = {
    "Y_shape": list(Y_shape),
    "Cr_shape": list(Cr_shape),
    "Cb_shape": list(Cb_shape),
    "padding": padding,
    "huffman_codes": {str(k):v for k, v in codes.items()},
    }

  header_json = json.dumps(header, indent=2)
  header_bytes = header_json.encode('utf-8')
    
  with open(filename, 'wb') as f:
    f.write(struct.pack('>I', len(header_bytes)))
    f.write(header_bytes)
    f.write(S_bytes)

#---------------------------------------------------------------------------------------------------

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

image = cv.imread('Hr_Image.jpg', cv.IMREAD_COLOR)
image = cv.cvtColor(image, cv.COLOR_BGR2YCrCb)
Y, Cr, Cb = cv.split(image)

Cr_sub, Cb_sub = chroma_subsample_420(Cr, Cb)
indices = zigzag_indices(n=8)

Y_shape = Y.shape
Cr_shape = Cr_sub.shape
Cb_shape = Cb_sub.shape

Y_blocks = divide_blocks(Y)
Cr_blocks = divide_blocks(Cr_sub)
Cb_blocks = divide_blocks(Cb_sub)

Y_fft_blocks = [TwoDFFT(block) for block in Y_blocks]
Cr_fft_blocks = [TwoDFFT(block) for block in Cr_blocks]
Cb_fft_blocks = [TwoDFFT(block) for block in Cb_blocks]

Y_quantized = [quantize_block(block, Q_For_Y, threshold=2) for block in Y_fft_blocks]
Cr_quantized = [quantize_block(block, Q_For_Clr, threshold=300) for block in Cr_fft_blocks]
Cb_quantized = [quantize_block(block, Q_For_Clr, threshold=300) for block in Cb_fft_blocks]

Y_zigzag = [zigzag_scan(block, indices) for block in Y_quantized]
Cb_zigzag = [zigzag_scan(block, indices) for block in Cb_quantized]
Cr_zigzag = [zigzag_scan(block, indices) for block in Cr_quantized]


Y_zigzag = [[int(round(val)) for val in block] for block in Y_zigzag]
Cb_zigzag = [[int(round(val)) for val in block] for block in Cb_zigzag]
Cr_zigzag = [[int(round(val)) for val in block] for block in Cr_zigzag]


symbols = []
encoded_blocks = []

for blocks in [Y_zigzag, Cr_zigzag, Cb_zigzag]:
  for block in blocks:
    encoded = rle_encode(block)
    encoded_blocks.append(encoded)
    for (runcat, _) in encoded:
      symbols.append(runcat)

tree = Build_Huffman_tree(symbols)
codes = build_huffman_codes(tree)

codebook = codes
codebook = {stringify_symbol(sym): code for sym, code in codes.items()}

bitstream_parts = []
for block in encoded_blocks:
    for (runcat, val_bits) in block:
        bitstream_parts.append(codes[runcat] + val_bits)
bitstream = ''.join(bitstream_parts)

S_bytes, padding = Bits_to_Bytes(bitstream)

save_compressed_file('compressed_image.huff', S_bytes, padding, codes, Y_shape, Cr_shape, Cb_shape)

