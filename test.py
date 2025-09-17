import pdfplumber

def main():
    # load downloads/faction_idoneth_deepkin_battle_profiles.pdf
    with pdfplumber.open("downloads/faction_flesh-eater_courts_battle_profiles.pdf") as pdf:
        # create a debug image with all lines
        page = pdf.pages[0]
        im = page.to_image()
        im.draw_lines(page.lines, stroke="green", stroke_width=3)
        im.save("test_output.png")

if __name__ == "__main__":
    main()