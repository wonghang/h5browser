# h5browser
h5browser.py - A lightweight HDF5 browser

h5browser.py is a great HDF5 file browser and manipulation tool for command-line lovers.

# History

I wrote it in around 2016. [hdfview](https://www.hdfgroup.org/downloads/hdfview/) is too big and too slow for working on large datasets stored in HDF5.
As a result, I developed my tools to work on HDF5 datasets based on [python-h5py](http://docs.h5py.org/en/stable/). 

# Features

* Both viewing and editing
* Import numpy  seamlessly
* Work in console
* Behave like a Unix shell
* No need to learn anything if you are familiar with the Linux environment

# Usage

To view/edit an existing HDF5 file.

```
$ ./h5browser.py (file path)
```

For example

```
$ wget https://support.hdfgroup.org/ftp/HDF5/examples/files/exbyapi/h5ex_t_float.h5
$ ./h5browser.py h5ex_t_float.h5
```

All groups and datasets are similar to that of a Linux shell. Groups are like directories and dataset are like files.

```
Opening h5ex_t_float.h5 (read-only)...
/$ ls
DS1  
```

Run `cat` to print the dataset.

```
/$ cat DS1
(4, 7) dtype('<f8')
array([[0.        , 1.        , 2.        , 3.        , 4.        ,
        5.        , 6.        ],
       [2.        , 1.66666667, 2.4       , 3.28571429, 4.22222222,
        5.18181818, 6.15384615],
       [4.        , 2.33333333, 2.8       , 3.57142857, 4.44444444,
        5.36363636, 6.30769231],
       [6.        , 3.        , 3.2       , 3.85714286, 4.66666667,
        5.54545455, 6.46153846]])
```

Another example, a weights file saved by Tensorflow:

```python
    model.fit(train_images,train_labels,epochs=5)
    model.save_weights("tutorial2.h5",save_format="h5")
```

```
Opening tutorial2.h5 (read-only)...
/$ ls
dense    dense_1  flatten  
/$ cd dense
/dense$ ls
dense  
/dense$ cd dense
/dense/dense$ ls
bias:0    kernel:0  
/dense/dense$ cat kernel:0
(784, 64) dtype('<f4')
array([[ 0.0772962 , -0.19338852, -0.13282706, ..., -0.09300001,
        -0.02127767,  0.02764973],
       [-0.05653608,  0.02674323, -0.20886165, ..., -0.13362217,
        -0.09858277,  0.10386786],
       [ 0.06501382, -0.15380736, -0.18260488, ..., -0.19010518,
        -0.27840403,  0.10981963],
       ...,
       [-0.06540593, -0.02921904,  0.37529314, ...,  0.08969089,
        -0.30455917, -0.1159869 ],
       [-0.04030671, -0.05087845,  0.39998335, ...,  0.36339465,
        -0.04353769, -0.02802175],
       [ 0.03603026,  0.01451135,  0.06465898, ...,  0.02350434,
        -0.18395725,  0.11049288]], dtype=float32)
/dense/dense$ cat bias:0
(64,) dtype('<f4')
array([-0.01382094,  0.01966984, -0.3044741 ,  0.28935912, -0.45117697,
       -0.26225635, -0.2349784 ,  0.32696533,  0.37573525,  0.48141968,
        0.26653507, -0.18124288,  0.3490619 ,  0.28595474, -0.1347229 ,
        0.25691232,  0.50809646,  0.32512894,  0.30652598, -0.03814144,
       -0.05990382,  0.45164672, -0.06980705,  0.47263968, -0.2892999 ,
        0.3364676 ,  0.6464235 ,  0.42230776,  0.19809212,  0.13945337,
        0.08160123, -0.01448387,  0.36892456,  0.29198548,  0.52638614,
        0.28065762,  0.15076898, -0.03802311,  0.27711394,  0.24514385,
        0.19033495, -0.01304685,  0.6659123 ,  0.04241025,  0.27037898,
        0.03491036, -0.20407383,  0.3315163 ,  0.1431491 ,  0.27683935,
       -0.30968678, -0.01846381,  0.3326616 , -0.07987908,  0.37076595,
        0.08467072,  0.13781434, -0.01815011,  0.01372865, -0.07599439,
        0.12265752, -0.2405651 ,  0.059001  ,  0.270626  ], dtype=float32)
/dense/dense$ 
```

h5browser.py can also edit and manipulate the data. To do so, you must switch the opening mode into read-write mode by running:

```
Opening tutorial2.h5 (read-only)...
/$ rw
Opening tutorial2.h5 (read-write)...
/# 
```

If the file is opened in read-write mode, the prompt will show `#` instead of `$`. It is akin to the root account prompt in the Bash shell.

In read-write mode, you can create a new group by `mkdir`:

```
/# mkdir new_group
/# ls 
dense      dense_1    flatten    new_group  
/# 
```

h5browser.py integrates with numpy seamlessly as an import. You can create a dataset by another combination of numpy code.

```
/# cd new_group
/new_group# X = np.linspace(0,1,50)
/new_group# Y = np.cos(2*np.pi*X)
/new_group# ls 
X  Y  
/new_group# cat X
(50,) dtype('<f8')
array([0.        , 0.02040816, 0.04081633, 0.06122449, 0.08163265,
       0.10204082, 0.12244898, 0.14285714, 0.16326531, 0.18367347,
       0.20408163, 0.2244898 , 0.24489796, 0.26530612, 0.28571429,
       0.30612245, 0.32653061, 0.34693878, 0.36734694, 0.3877551 ,
       0.40816327, 0.42857143, 0.44897959, 0.46938776, 0.48979592,
       0.51020408, 0.53061224, 0.55102041, 0.57142857, 0.59183673,
       0.6122449 , 0.63265306, 0.65306122, 0.67346939, 0.69387755,
       0.71428571, 0.73469388, 0.75510204, 0.7755102 , 0.79591837,
       0.81632653, 0.83673469, 0.85714286, 0.87755102, 0.89795918,
       0.91836735, 0.93877551, 0.95918367, 0.97959184, 1.        ])
/new_group# cat Y
(50,) dtype('<f8')
array([ 1.        ,  0.99179001,  0.96729486,  0.92691676,  0.8713187 ,
        0.80141362,  0.71834935,  0.6234898 ,  0.51839257,  0.40478334,
        0.28452759,  0.1595999 ,  0.03205158, -0.09602303, -0.22252093,
       -0.34536505, -0.46253829, -0.57211666, -0.67230089, -0.76144596,
       -0.8380881 , -0.90096887, -0.94905575, -0.98155916, -0.99794539,
       -0.99794539, -0.98155916, -0.94905575, -0.90096887, -0.8380881 ,
       -0.76144596, -0.67230089, -0.57211666, -0.46253829, -0.34536505,
       -0.22252093, -0.09602303,  0.03205158,  0.1595999 ,  0.28452759,
        0.40478334,  0.51839257,  0.6234898 ,  0.71834935,  0.80141362,
        0.8713187 ,  0.92691676,  0.96729486,  0.99179001,  1.        ])
```

To delete a data, use `rm` like Unix shell:

```
/new_group# rm X
/new_group# ls
Y  
```

However, to delete a group, you also use `rm` instead:

```
/new_group# cd ..
/# rm new_group
/# ls
dense    dense_1  flatten  
/# 
```

Once you finish editing the HDF5 file, you can switch back to read-only mode by `ro`:

```
/# ro
Opening tutorial2.h5 (read-only)...
/$ a = 123
This command requires read-write mode. Please switch to read-write mode using command "rw" first
/$ 
```

and then you are no longer able to modify its content.

Attributes under a group can be read by `pwd`:

```
/xxx/RESULT$ pwd
/xxx/RESULT
count => 12
```

At last, you can also create a new HDF5 file by opening a path that doesn't exist:

```
$ h5browser.py /tmp/a.h5
Opening /tmp/a.h5 (read-only)...
/tmp/a.h5 not found. Do you want to create it [y/n]? y
Opening /tmp/a.h5 (read-write)...
/#
```

