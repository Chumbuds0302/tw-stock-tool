import twstock

def check_twstock_name(code):
    if code in twstock.codes:
        print(f"Code: {code}")
        print(f"Name (repr): {repr(twstock.codes[code].name)}")
    else:
        print(f"Code {code} not found in twstock.codes")

if __name__ == "__main__":
    code = "2330"
    if code in twstock.codes:
        name = twstock.codes[code].name
        print(f"Original repr: {repr(name)}")
        try:
            fixed_name = name.encode('latin1').decode('big5')
            print(f"Fixed name: {fixed_name}")
        except Exception as e:
            print(f"Fix failed: {e}")
