import markdown


def txt2html(text):
    return markdown.markdown(text)

# print markdown.markdownFromFile()
print txt2html('''
```
ls
ls
ls
if njnjj
```
''')