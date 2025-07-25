import numpy as np
import matplotlib.pyplot as plt
import cv2 as cv


def PowerOfTwo(x):
  return 1 << (x - 1).bit_length()

def FFT(signal):
  N = len(signal)

  if not(N & (N - 1) == 0) and N != 0:
    New_N = PowerOfTwo(N)
    New_Signal = np.zeros(New_N, dtype=complex)
    New_Signal[:N] = signal
    signal = New_Signal
    N = New_N
  if N == 1:
    return signal
  else:
    Even_Part = FFT(signal[::2])
    Odd_Part = FFT(signal[1::2])
    Factor = np.exp(-2j * np.pi * np.arange(N//2) / N)
    signal = np.concatenate([
      Even_Part + Factor * Odd_Part, Even_Part - Factor * Odd_Part
    ])
  return signal

def TwoDFFT(image):
  FFT_Rows = np.array([FFT(row) for row in image])
  return np.array([FFT(col) for col in FFT_Rows] )
def RGBFFT(image):
  R, G, B = image[:, :, 0], image[:, :, 1], image[:, :, 2]
    
  R_fft = TwoDFFT(R)
  G_fft = TwoDFFT(G)
  B_fft = TwoDFFT(B)

  return R_fft, G_fft, B_fft

def Quantize(image_fft, Q_matrix):
  h, w = image_fft.shape
  H, W = Q_matrix.shape
  quantized = np.zeros_like(image_fft)

  for i in range(0, h, H):
    for j in range(0, w, W):
      block = image_fft[i:i+H, j:j+W]
      if block.shape == Q_matrix.shape:
        quantized[i:i+H, j:j+W] = np.round(block / Q_matrix)
  return quantized

image = cv.imread('Hr_Image.jpg', cv.IMREAD_COLOR)
image = cv.cvtColor(image, cv.COLOR_BGR2RGB)

R_fft, G_fft, B_fft = RGBFFT(image)


limit = 1000
R_fft[np.abs(R_fft) < limit] = 0
G_fft[np.abs(G_fft) < limit] = 0
B_fft[np.abs(B_fft) < limit] = 0

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

R_fft = Quantize(R_fft, Q_matrix).astype(np.int16)
G_fft = Quantize(G_fft, Q_matrix).astype(np.int16)
B_fft = Quantize(B_fft, Q_matrix).astype(np.int16)

np.savez("RGB_Compressed.npz", R=R_fft, G=G_fft, B=B_fft, shape=image.shape)