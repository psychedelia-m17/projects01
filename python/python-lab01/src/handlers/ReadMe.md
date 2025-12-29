# Implementing Factory

## Abstract Base Classes
In Python, `abc` stands for Abstract Base Classes.  
It is a built-in module that provides the infrastructure for defining classes that
cannot be instantiated on their own and are intended to be blueprints for other
classes.


### Key Concepts

- Abstract Base Class (ABC): A class that defines a set of methods that subclasses must implement.  
- Abstract Method: A method declared in an ABC but lacking an implementation.  
- It is marked with the `@abstractmethod` decorator.  
Instantiation Restriction: Python prevents you from creating an instance of any class that has unimplemented abstract methods. 

### Why Use ABCs?

- **Enforce Interfaces**: They ensure that different subclasses provide the same set of methods, creating a
consistent "contract" for your code.
- **Design Blueprint**: They help organize large projects by defining a clear structure for developers to follow.
- **Polymorphism**: They allow functions to work with any object that follows a specific ABC "template," regardless of the specific subclass. 

### Example of ABC

```python
from abc import ABC, abstractmethod

class Shape(ABC):
    @abstractmethod
    def area(self):
        pass

class Circle(Shape):
    def __init__(self, radius):
        self.radius = radius

    def area(self):
        return 3.14 * (self.radius ** 2)

# This would raise a TypeError because area() is not implemented:
# s = Shape() 

c = Circle(5)
print(c.area())  # Output: 78.5
```

### Common Built-in ABCs

Python's collections.abc module contains several predefined ABCs used for testing object types: 
`Iterable`: For objects that support for loops.
`Sized`: For objects that have a length (support len()).
`Mapping`: For dictionary-like objects.
`Sequence`: For list-like or tuple-like objects.
