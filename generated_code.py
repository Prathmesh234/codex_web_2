```python
# Open the generated_code.py file for reading
with open('generated_code.py', 'r') as file:
    lines = file.readlines()

# Open the file again for writing to modify it
with open('generated_code.py', 'w') as file:
    for line in lines:
        # Replace the line containing the number with 10
        if "factorial(" in line:
            file.write("print(factorial(10))\n")
        else:
            file.write(line)
```