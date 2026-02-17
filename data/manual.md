# S.A.G.A. Database User Manual

Welcome to the **S.A.G.A. (Simulator & Lore Engine) Database**. This tool is designed to help you build, manage, and export complex world lore, timelines, and celestial systems.

---

## 1. The Codex (Wiki)
The Codex is the heart of the database. It allows you to create articles for characters, locations, factions, and items.

*   **Creating Articles**: Click `+ New Article` in the Sidebar.
*   **Searching**: Use the search bar in the sidebar to filter by name or category.
*   **Markdown Support**: The Lore text area supports standard Markdown (Headers, Lists, Spacers). Use the `Preview` tab to see how it looks.

## 2. Categories & Templates
Use the **Category Builder** to define custom data fields for different types of articles.

*   **Templates**: Create a "Faction" template with fields like *Population* or *Color*.
*   **Fields**: Add text, numbers, sliders, or image paths.
*   **Sprite Refs**: Use these to link an image to the Replay Viewer (Projector).

## 3. The Timekeeper (Calendar)
Manage your world's time flow and celestial bodies.

*   **Structure**: Define months, day lengths, and weekdays.
*   **Moons**: Add multiple moons with custom cycles and phases. These affect simulation events.
*   **Seasons**: Set up seasonal shifts that drive the Climate Engine.

## 4. HTML Export
Generate a professional-looking web wiki from your data.

*   Click `Export HTML` on any article to generate an `export/` folder.
*   The generated site includes an index and inter-linked article pages.
*   Use this to share your world-building with others!

## 5. Simulation Integration
You can now define articles as active simulation entities by using the **Simulation Identity** block.

- **Agents**: Define biology (temp/moisture), behavior (aggression/expansion), and social types.
- **DNA Tables**: Use Diet and Biome preference tables for seek/avoid logic.
- **Production**: Set living and harvest resource outputs.
- **Factions**: Link founding events and formation dates.
- **Biomes**: Create custom terrain overrides with temp/moisture modifiers.

## Tips & Tricks
- Use **Tags** to organize your world building.
- Link articles to cell locations to see gold circles on the **World Timeline**.
- Export to **HTML** to share your world with others!

## 6. Simulation Integration
Articles can be linked to active simulation entities via `Sim ID`. 

---
*Created by the S.A.G.A. Development Team.*
