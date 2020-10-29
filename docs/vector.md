## Class: Vector

Simple 2D vector class to make vector operations more convenient. If performance is a concern, you are probably better off looking at numpy.

Supports the following operations:
  
* Initialization from two arguments, two keyword  arguments (`x` and `y`),
tuple, list, or another Vector.
* Equality and unequality comparisons to other vectors. For floating point
numbers, equality tolerance is 1e-10.
* `abs`, `int` and `round`
* Addition and in-place addition
* Subtraction
* Multiplication and division by a scalar
* `len`, which is the same as `magnitude`, see below.

Sample usage:
  
    from ui3.vector import Vector
    
    v = Vector(x = 1, y = 2)
    v2 = Vector(3, 4)
    v += v2
    assert str(v) == '[4, 6]'
    assert v / 2.0 == Vector(2, 3)
    assert v * 0.1 == Vector(0.4, 0.6)
    assert v.distance_to(v2) == math.sqrt(1+4)
  
    v3 = Vector(Vector(1, 2) - Vector(2, 0)) # -1.0, 2.0
    v3.magnitude *= 2
    assert v3 == [-2, 4]
  
    v3.radians = math.pi # 180 degrees
    v3.magnitude = 2
    assert v3 == [-2, 0]
    v3.degrees = -90
    assert v3 == [0, -2]

## Methods


#### `dot_product(self, other)`

  Sum of multiplying x and y components with the x and y components of another vector. 

#### `distance_to(self, other)`

  Linear distance between this vector and another. 

#### `polar(self, r, m)`

  Set vector in polar coordinates. `r` is the angle in radians, `m` is vector magnitude or "length". 

#### `steps_to(self, other, step_magnitude=1.0)`

  Generator that returns points on the line between this and the other point, with each step separated by `step_magnitude`. Does not include the starting point. 

#### `rounded_steps_to(self, other, step_magnitude=1.0)`

  As `steps_to`, but returns points rounded to the nearest integer. 
## Properties


#### `x (get)`

  x component of the vector. 

#### `y (get)`

  y component of the vector. 

#### `magnitude (get)`

  Length of the vector, or distance from (0,0) to (x,y). 

#### `radians (get)`

  Angle between the positive x axis and this vector, in radians. 

#### `degrees (get)`

  Angle between the positive x axis and this vector, in degrees. 
