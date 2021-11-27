import midgy



while True:
    text = input('midgy > ')
    if text.strip() == "": continue
    result, error = midgy.run('<stdin>',text)

    if error: print(error.as_string())
    elif result:
        if len(result.elements) == 1:
            print(repr(result.elements[0]))
        print(repr(result))

# import comparison
# while True:
#     text = input('midgy > ')
#     result, error = comparison.run('<stdin>',text)

#     if error: print(error.__str__())
#     elif result: print(result)
