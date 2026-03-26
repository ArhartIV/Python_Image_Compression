<h1>Custom Image Compression</h1>

This is one of my personal projects, that I did to better understand the algorithms and real-world applications   
of Fast Fourier Transform  and Image processing. 

<h3>Effectiveness</h3>
My Compression algorithm is pretty close to the actual Jpeg algorithm, but it puts the compression before keeping the higher resolution.  Jpeg also uses the DCT transform opposed to FFT transform.
 On average, the .huff compressed file weighs around 10-40% less than jpeg one, but with a higher drop off in quality compared to Jpeg.   <br>

<br>
 the Difference comes from a more aggressive threshholding and quantization Matrix, and a little bit different Huffman encoding.

<h3>Examples</h3>

<div style="border: 2px solid #aaa; border-radius: 10px; padding: 20px; margin: 20px 0; max-width: 1300px;">
  <div style="display: flex; gap: 20px; align-items: flex-start; justify-content: center;">
    <div style="text-align: center;">
      <img src="Mountains.jpg" alt="Original Mountains" width="500"/>
      <div>Original (Mountains.jpg)</div>
    </div>
    <div style="text-align: center;">
      <img src="Mountains_rec.jpg" alt="Reconstructed Mountains" width="500"/>
      <div>Reconstructed (Mountains_rec.jpg)</div>
    </div>
  </div>
  <div style="text-align: center; margin-top: 18px; font-size: 1.1em;">
    <b>Mountains.huff</b> file weighs <b>4 133 kb</b> as opposed to original <b>10 092kb</b>
  </div>
</div>

<div style="border: 2px solid #aaa; border-radius: 10px; padding: 20px; margin: 20px 0; max-width: 1300px;">
  <div style="display: flex; gap: 20px; align-items: flex-start; justify-content: center;">
    <div style="text-align: center;">
      <img src="city.jpg" alt="Original Mountains" width="500"/>
      <div>Original (city.jpg)</div>
    </div>
    <div style="text-align: center;">
      <img src="city_rec.jpg" alt="Reconstructed Mountains" width="500"/>
      <div>Reconstructed (city_rec.jpg)</div>
    </div>
  </div>
  <div style="text-align: center; margin-top: 18px; font-size: 1.1em;">
    <b>city.huff</b> file weighs <b>1 972kb</b> as opposed to original <b>4 082kb</b>
  </div>
</div>

<div style="border: 2px solid #aaa; border-radius: 10px; padding: 20px; margin: 20px 0; max-width: 1300px;">
  <div style="display: flex; gap: 20px; align-items: flex-start; justify-content: center;">
    <div style="text-align: center;">
      <img src="Colorful_Image.jpg" alt="Original Mountains" width="500"/>
      <div>Original (Colorful_Image.jpg)</div>
    </div>
    <div style="text-align: center;">
      <img src="colorful_rec.jpg" alt="Reconstructed Mountains" width="500"/>
      <div>Reconstructed (colorful_rec.jpg)</div>
    </div>
  </div>
  <div style="text-align: center; margin-top: 18px; font-size: 1.1em;">
    <b>colorful_comp.huff</b> file weighs <b>470kb</b> as opposed to original <b>1 452kb</b>
  </div>
</div>

<div style="border: 2px solid #aaa; border-radius: 10px; padding: 20px; margin: 20px 0; max-width: 1300px;">
  <div style="display: flex; gap: 20px; align-items: flex-start; justify-content: center;">
    <div style="text-align: center;">
      <img src="food.jpg" alt="Original Mountains" width="500"/>
      <div>Original (Food.jpg)</div>
    </div>
    <div style="text-align: center;">
      <img src="food_rec.jpg" alt="Reconstructed Mountains" width="500"/>
      <div>Reconstructed (food_rec.jpg)</div>
    </div>
  </div>
  <div style="text-align: center; margin-top: 18px; font-size: 1.1em;">
    <b>food.huff</b> file weighs <b>2 195kb</b> as opposed to original <b>6 414kb</b>
  </div>
</div>

*All pictures were taken from open website Freepik.com, that states they are free of copyrights. 

<h3>Use</h3>
Format for calling the Compression from Terminal: 

```
  python Image_Compress.py city.jpg -o test.huff
```

Format for calling the Decompression from Terminal:
```
  python Image_Decompress.py test.huff -o test_rec.jpg
```
A similar algorithm can be used in fields, where the size of a file is crucial, such as sending an image faster   
on social media, satellite data and etc. The code also can be easily be rewritten in C or C++ for further use in signal  
processing or in a microprocessor. It is possible to speed-up the algorithm if you use np.fft.fft instead of my Custom implementation, i just wanted to write my own to understand how it works internally.  