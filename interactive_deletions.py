#!/usr/bin/env python3
from pathlib import Path

# Files to delete (review before running)
FILES = [
    r'''C:\Users\burt_\Downloads\Am I Tempting You - Pornhubcom.mp4''',
    r'''C:\Users\burt_\Downloads\Boob Physics - Pornhubcom.mp4''',
    r'''C:\Users\burt_\Downloads\Cute Curvy  Natural Blackgirl Enjoys High Level Submissive BDSM(Ful Video on Myclublink on Insta - Pornhubcom.mp4''',
    r'''C:\Users\burt_\Downloads\Shaking Big Tits on Cam - Pornhubcom.mp4''',
    r'''C:\Users\burt_\Downloads\Bound plaything enjoyment - Upornia com (1).mp4''',
    r'''C:\Users\burt_\Downloads\Do I have an Hourglass - Pornhubcom.mp4''',
    r'''C:\Users\burt_\Downloads\Full Video - 4K Haley Hanks Loves To Wash Her Huge Tits In The Sink Take A Look  Pornhub.mp4''',
    r'''C:\Users\burt_\Downloads\Shacking Big Natural Tits Bouncing Saggy Tits Horny MILF - Pornhubcom.mp4''',
    r'''C:\Users\burt_\Downloads\Full Video - THE LESBIAN EXPERIENCE - ANNA BELL PEAKS DOMINATES ADRIA RAE  Pornhub.mp4''',
    r'''C:\Users\burt_\Downloads\Leilani Gold wants to try Bondage Fuck with her Boyfriend 1 - Pornhubcom.mp4''',
    r'''C:\Users\burt_\Downloads\Massaging my Big Natural Breast - Pornhubcom.mp4''',
    r'''C:\Users\burt_\Downloads\Rescued_video_ 2025-08-17 04_25.mp4''',
    r'''C:\Users\burt_\Downloads\Rescued_video_ 2025-08-17 04_43.mp4''',
]

def main():
    for p in FILES:
        try:
            Path(p).unlink()
            print('Deleted', p)
        except Exception as e:
            print('Failed to delete', p, '->', e)

if __name__ == '__main__':
    main()

# Summary: 13 files, 546.3 MB freed
