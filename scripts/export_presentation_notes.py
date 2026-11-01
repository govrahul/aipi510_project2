"""Export the delivered slide titles and notes without requiring PowerPoint."""
from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
A='{http://schemas.openxmlformats.org/drawingml/2006/main}'


def main():
    deck=ROOT/'deliverables/project2_presentation.pptx'
    lines=['# Project 2 presentation script','',
           'Nine slides with a target duration of 7 minutes 5 seconds. Rehearse aloud and leave room within the eight minute limit. Source references follow each speaking passage; they need not be read aloud. Speaking roles are for the authors to choose.','']
    with zipfile.ZipFile(deck) as archive:
        for i in range(1,10):
            slide=ET.fromstring(archive.read(f'ppt/slides/slide{i}.xml'))
            # The first textbox is the slide title in this builder.
            first_shape=slide.find('.//{http://schemas.openxmlformats.org/presentationml/2006/main}sp')
            title=' '.join(t.text or '' for t in first_shape.findall('.//'+A+'t'))
            notes=ET.fromstring(archive.read(f'ppt/notesSlides/notesSlide{i}.xml'))
            text='\n'.join(t.text or '' for t in notes.findall('.//'+A+'t'))
            lines.extend([f'## Slide {i} {title}', '',text,''])
    (ROOT/'deliverables/presentation_script.md').write_text('\n'.join(lines))


if __name__=='__main__':main()
