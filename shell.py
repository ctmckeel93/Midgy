import midgy



while True:
    text = input('midgy > ')
    result, error = midgy.run('<stdin>',text)

    if error: print(error.as_string())
    elif result: print(result)

# import comparison
# while True:
#     text = input('midgy > ')
#     result, error = comparison.run('<stdin>',text)

#     if error: print(error.__str__())
#     elif result: print(result)
