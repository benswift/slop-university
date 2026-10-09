---
title: Segmentation network learns to say how sharp an edge is
subtitle: A soil surveyor's four words for a boundary are taught to an image model using 312 patches airbrushed onto one mannequin
date: 2026-10-10
description: A research poster from the School of Underlying Conditions gives a lesion-segmentation network a second output, borrowed from soil description, that reports how gradually an outline arrives.
output: slop-poster-where-a-plaque-tefs3b
---

Image models that outline a patch of skin return a line. The School of
Underlying Conditions has asked one to return, as well, a word for what kind of
line it is. _Where a Plaque Ends_, a research poster by Dr Brynjar Obiora,
Senior Research Fellow, and Dr Vigdis Emenike, Senior Lecturer, takes the four
terms a soil surveyor writes beside a boundary in a pit (abrupt, clear, gradual,
diffuse) and trains a network to assign them along its own outline.

> I have written those four words in a field notebook some thousands of times
> without once supposing they could be of use to anybody indoors. It is a
> pleasant thing to have a habit turn out to be portable.
>
> --- Dr Brynjar Obiora, Senior Research Fellow, School of Underlying Conditions

No skin was involved. The authors airbrushed 312 red patches onto a display
mannequin, setting the softness of each edge by how far back the nozzle was
held, and photographed every patch twenty times under shifting lamps. Because
the edges were painted to order, each of the 6,240 photographs came with its
answer attached. On patches it had not seen, the network named the painted
class for 77% of boundary segments, and nearly all of its mistakes landed one
class away. Where the mannequin's surface curved off from the camera, it tended
to report an edge as sharper than it was.

The University sees in the poster a school willing to lend its vocabulary as
readily as its instruments, and an encouraging early exchange between its earth
sciences and its interest in learned systems. Dr Emenike said the mannequin "has
been an uncomplaining colleague, and has asked for nothing but a dust sheet."

The poster makes no statement about disease or its treatment. It is available
from the University's research repository under an open licence,
doi:10.5555/slop.tefs3b.
