import numpy as np
import matplotlib.pyplot as plt
import cv2 as cv

#Find the closest Power of Two
def PowerOfTwo(x):
  return 1 << (x - 1).bit_length()

#Basic IFFT
def Inverse_FFT(Transform):
  N = len(Transform)
  if not (N & (N - 1) == 0) and N != 0:
     New_N = PowerOfTwo(N)
     New_T = np.zeros(New_N, dtype=complex)
     New_T[:N] = Transform
     N = New_N
     Transform = New_T

  if N == 1:
    return Transform
  else:
    Even_part = Inverse_FFT(Transform[::2])
    Odd_Part = Inverse_FFT(Transform[1::2])
    Factor = np.exp(2j * np.pi * np.arange(N//2)/N)
    return np.concatenate([Even_part + Factor * Odd_Part,
                           Even_part - Factor * Odd_Part])/2

#IFFT for two dims
def Inverse_TwoDFFT(spectrum):
    cols = np.array([Inverse_FFT(col) for col in spectrum])
    return np.array([Inverse_FFT(row) for row in cols])

#Removes the zeroes that could be added during compression 
def Remove_Padding(image):
    row_mask = ~np.all(image == 0, axis=(1, 2))
    col_mask = ~np.all(image == 0, axis=(0, 2))
    image_no_padding = image[row_mask][:, col_mask]

    return image_no_padding

def Dequantize(quantized, Q_matrix):
  h, w = quantized.shape
  H, W = Q_matrix.shape
  dequantized = np.zeros_like(quantized)

  for i in range(0, h, H):
    for j in range(0, w, W):
      block = quantized[i:i+H, j:j+W]
      if block.shape == Q_matrix.shape:
        dequantized[i:i+H, j:j+W] = block * Q_matrix
  return dequantized

data = np.load("RGB_Compressed.npz")
R_fft = data['R']
G_fft = data['G']
B_fft = data['B']
original_shape = data['shape']

Q_matrix = np.array([
    [16,16,16,16,16,16,16,16],
    [12,12,14,16,16,16,16,16],
    [14,13,16,24,24,24,24,16],
    [14,17,22,24,24,24,16,14],
    [14,22,16,24,24,16,16,14],
    [12,16,16,64,16,16,16,14],
    [12,16,16,16,16,16,16,16],
    [16,16,16,16,16,16,16,16]
])

M = 64
Q_matrix = np.zeros((M, M))

for i in range(M):
  for j in range(M):
    Q_matrix[i, j] = 512

#Reconstruct each spectrum
R_rec = Dequantize(Inverse_TwoDFFT(R_fft), Q_matrix)
G_rec = Dequantize(Inverse_TwoDFFT(G_fft), Q_matrix)
B_rec = Dequantize(Inverse_TwoDFFT(B_fft), Q_matrix)

reconstructed = np.stack((R_rec, G_rec, B_rec), axis=2)
reconstructed = np.real(reconstructed)
reconstructed = np.clip(reconstructed, 0, 255).astype(np.uint8)
Final_Image = Remove_Padding(reconstructed)

plt.figure(figsize=(10, 6))
plt.imshow(Final_Image, cmap='gray')
plt.axis('off')
plt.savefig('Reconstructed_Image_2.png')
plt.show()