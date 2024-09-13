# Oridesk - Origami Tool for Autodesk Maya

## What's Oridesk?
Is a tool for implementing origami rigs in Autodesk Maya, based on the "crease pattern" theory.
> I recomend reading _Lang, R. J. (2004). Origami design secrets: mathematical methods for an ancient art._ for more information about Origami Mathematical Theory.

## Why "*Ori*" desk?
The name cames from the Oriedita software, an amazing tool made for crease pattern creation. When I read the Robert J. Lang book I was fastinated with the complexity of the origami art, and I started to make my own patterns in paper. I thought that combining this hobby with my 3D art passion could be an exciting project and an amazing contribution to both communities. That's why Oridesk become an implementation project for Oriedita patterns in Maya.

## Start with OriDesk
Oridesk works with SVG patterns, so you need a **.svg** file to start working. It could be made in any software with SVG exporting like Illustrator, but I recommend using Oriedita if you're interested in more complex patterns (or if you're an origami freak as me 😎).

> [!NOTE]
> For now, is only available for Oriedita's SVG files, since other SVG files may have different text extructure to be parsed.

If you want to try the tool without downloading Oriedita, I leave an SVG example file, the one that I'm using for the development.

## Development
_Last update: 09/06/24_

![image](https://github.com/user-attachments/assets/c684b0c1-733a-4fa0-837f-981c88f734ba)

There are a lot of little details that I want to improve, but as a first experience rendering GL with PyQt everything is going well 😙.

**TO DO**
- [ ] Set Widget size
- [ ] Set crease pattern margin (I hate that it renders at the edge)
- [ ] Make paintGL() call at initialization (pattern doesn't show at first)
- [ ] Make lines selectable
- [ ] Make 3D view

## Reference links and information
[Robert J. Lang Website](https://langorigami.com/)

[Oriedita Website](https://oriedita.github.io/)
