#pdfparser

[![Build Status](https://travis-ci.org/izderadicka/pdfparser.svg?branch=master)](https://travis-ci.org/izderadicka/pdfparser)

Python binding for libpoppler - focused on text extraction from PDF documents.

Intended as an easy to use replacement for [pdfminer](https://github.com/euske/pdfminer), 
which provides much better performance (see below for short comparison) and is Python3 compatible.

See this [article](http://zderadicka.eu/parsing-pdf-for-fun-and-profit-indeed-in-python/)
for some comparisons with pdfminer and other approaches. 


Binding is written in [cython](http://cython.org/).

Requires recent libpoppler >= 0.40 - so I'd recommend to build it from source to get latest library, 
but it works also with recent libpoppler library present in common linux distributions (then it requires 
dev package to build). See below for installation instructions.


Available under GPL v3 or any later version license (libpoppler is also GPL).

## How to install

Below or some instructions to install this package


### Debian like -  system wide libpoppler 
```
sudo apt-get update
sudo apt-get install -y libpoppler-private-dev libpoppler-cpp-dev
pip install cython
pip install git+https://github.com/nghiapq77/pdfparser
```

### Mac OS
```
pip install cython
pip install git+https://github.com/nghiapq77/pdfparser
```


## Speed comparisons

|                             | pdfreader     | pdfminer      |speed-up factor|
| --------------------------- | ------------- | ------------- |---------------|
| tiny document (half page)   | 0.033s        | 0.121s        | 3.6 x         |
| small document (5 pages)    | 0.141s        | 0.810s        | 5.7 x         |
| medium document (55 pages)  | 1.166s        | 10.524s       | 9.0 x         |       
| large document (436 pages)  | 10.581s       | 108.095s      | 10.2 x        |


pdfparser code used in test

    import pdfparser.poppler as pdf
    import sys
    
    d=pdf.Document(sys.argv[1])
    
    print('No of pages', d.no_of_pages)
    for p in d:
        print('Page', p.page_no, 'size =', p.size)
        for f in p:
            print(' '*1,'Flow')
            for b in f:
                print(' '*2,'Block', 'bbox=', b.bbox.as_tuple())
                for l in b:
                    print(' '*3, l.text.encode('UTF-8'), '(%0.2f, %0.2f, %0.2f, %0.2f)'% l.bbox.as_tuple())
                    #assert l.char_fonts.comp_ratio < 1.0
                    for i in range(len(l.text)):
                        print(l.text[i].encode('UTF-8'), '(%0.2f, %0.2f, %0.2f, %0.2f)'% l.char_bboxes[i].as_tuple(),\
                            l.char_fonts[i].name, l.char_fonts[i].size, l.char_fonts[i].color,)
                    print()
                    
## How to modify parsing algorithm?

As you probably know PDF is document format intended for printing, so all logical structure of the text 
is lost (paragraphs, columns, tables, etc.). libpoppler is trying to reconstruct some of this logical 
structure of the document back by comparing physical positions of characters on the page and their mutual
distances and reconstructing back words, lines, paragraphs, columns.  


Component which is responsible for this reconstruction is C++ class `TextOutputDev` (in poppler/TextOutputDev.cc). 
It's using many constants for this jobs, vast majority of constants in hardcoded into code.
Actually the only parameter that is available to Python code is combination of parameters `phys_layout` and
`fixed_pitch`, which influences how text is ordered into columns. If you put `phys_layout` to True and
`fixed_pitch` to value > 0, then `fixed_pitch` will be used as maximum distance between words in a line and 
minimum distance between columns (in pixels).  I think `phys_layout` also influences order of boxes 
in page iteration. However influence of these parameters is not quite straight forward - so you'll need to 
experiment to see how it works in your case.


Another problem I encoutered is vertical spacing between lines in single box (paragraph) - this parameter 
is unfortunatelly fixed in libpoppler - it's constant `maxLineSpacingDelta` in poppler/TextOutputDev.cc, which 
is set to 1.5 (font size).  If you need to accept bigger line spacing in paragraph then, you'll have to change it
in C++ code and recompile libpoppler (in this case I recommend to make library local to pdfparser package). 
I've tried with value 2.0 and it seems to work fine.

