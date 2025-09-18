from PIL import Image, ImageDraw

def tobytes_flipped(fn, id):
  #image = Image.open(fn).convert('1')
  image=fn
  print("\n"
        "#define {id}_width  {w}\n"
        "#define {id}_height {h}\n"
        "\n"
        "const uint8_t PROGMEM {id}_data[] = {{\n"
        .format(id=id, w=image.width, h=image.height), end='')
  for y in range(0, image.height):
    for x in range(0, (image.width + 7)//8 * 8):
      if x == 0:
        print("  ", end='')
      if x % 8 == 0:
        print("", end='')
        #print("B", end='')

      bit = '0'
      if x < image.width and image.getpixel((x,y)) != 0:
        bit = '1'
      print(bit, end='')

      if x % 8 == 7:
        print(",", end='')
    print()
  print("};")

def tobytes(fn, id):
  #image = Image.open(fn).convert('1')
  image=fn
  print("\n"
        "#define {id}_width  {w}\n"
        "#define {id}_height {h}\n"
        "\n"
        "const uint8_t PROGMEM {id}_data[] = {{\n"
        .format(id=id, w=image.width, h=image.height), end='')
  for x in range(0, (image.width + 7)//8 * 8):
    for y in range(0, image.height):
      if y == 0:
        print("  ", end='')
      if y % 8 == 0:
        print("", end='')
        #print("B", end='')

      bit = '0'
      if y < image.width and image.getpixel((x,y)) != 0:
        bit = '1'
      print(bit, end='')

      if y % 8 == 7:
        print(",", end='')
    print()
  print("};")

def tohex(fn, id):
  image=fn
  for x in range(0, (image.width + 7)//8 * 8):
    byte=""
    for y in range(0, image.height):
      bit = "0"
      if y < image.width and image.getpixel((x,y)) != 0:
        bit = "1"
      byte=byte+bit
         
      if y % 8 == 7:
        print(hex(int(byte,2)),end=' ')
        print(",", end='')
        byte=""
    print()
  
with Image.open("logo.bmp") as im:

    draw = ImageDraw.Draw(im)
    draw.line((0, 0) + im.size, fill=128)
    draw.line((0, im.size[1], im.size[0], 0), fill=128)

    ib=im.tobytes()

   # tobytes(im, 'splash2')
    tohex(im, 'splash2')

