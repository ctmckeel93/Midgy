import midgy

while True:
    text = input('midgy > ')
    result, error = midgy.run('<stdin>',text)

    if error: print(error.__str__())
    else: print(result)