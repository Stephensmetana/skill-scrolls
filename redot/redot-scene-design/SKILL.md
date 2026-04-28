---
name: redot-scene-design
description: Redot 4 scene structure and boundaries. Triggers on "how should I structure this scene", "should this be its own scene", "what nodes do I need for X", "is my scene too big", scene boundary decisions. Covers self-containment, when to split, node hierarchy, @export injection, folder organization.
---

# Redot Scene Design Guide

Scenes are Redot's primary unit of composition — the equivalent of a class or component in OOP. Good scene design means each scene can be instantiated anywhere, makes no assumptions about its environment, and owns everything it needs to function.

This skill covers the *design* of individual scenes. For cross-scene communication and autoload architecture, use `redot-architecture`.

---

## The Core Principle: Scenes Are Self-Contained Units

A scene should work in isolation. If you can't run a scene by pressing F6 on it without crashing, it has external dependencies it shouldn't have.

Ask yourself before building a scene:
- Does this scene assume a specific parent exists?
- Does this scene use hardcoded node paths to siblings or cousins?
- Does this scene call `get_parent()` or `get_node("../../SomethingElse")`?

If the answer to any of these is yes, the scene is too tightly coupled. Refactor using `@export` or signals.

---

## When to Make a New Scene

Split into a new scene when:
- The group of nodes will be **reused** elsewhere (even once)
- The group of nodes has **its own state and logic** (it's a "thing", not just visual layout)
- You want to be able to **swap it out** independently (e.g., different enemy types)
- It gets **instantiated at runtime** (enemies, projectiles, pickups, UI panels)

Keep nodes in the same scene when:
- They have no meaning independent of each other
- They are purely visual/structural children (e.g., a Sprite2D and a CollisionShape2D that together form one object)
- Separating them would just create an empty wrapper scene

**Rule of thumb:** If you find yourself writing `preload("res://...")` to reference a sibling, that sibling should probably be its own scene.

---

## The "No Dependencies" Rule

From the official Godot docs: *"If at all possible, you should design scenes to have no dependencies. That is, you should create scenes that keep everything they need within themselves."*

When a scene absolutely must receive external data, use one of these two patterns — in this priority order:

### 1. @export (Preferred for simple values and resources)

```gdscript
# Door.gd
@export var required_key: ItemData   # wired in the inspector by a designer
@export var open_sound: AudioStream

func interact(_player):
    if InventoryManager.has_item_by_resource(required_key):
        _play_sound(open_sound)
        _open()
```

`@export` makes the dependency visible in the editor. A designer can wire it up without touching code. It also means the dependency is declared at the top of the script — readable, explicit, not hidden in `_ready()`.

### 2. Setter Injection (for runtime wiring by a parent)

```gdscript
# HealthBar.gd
func setup(health_signal: Signal) -> void:
    health_signal.connect(_on_health_changed)

# Game.gd (the parent wires its children)
func _ready():
    $HealthBar.setup($Player.health_changed)
```

The HealthBar doesn't know where the Player is. The Game scene — which owns both — wires them. This is "call down, signal up" applied to setup.

### Never: Hardcoded Paths

```gdscript
# BAD — breaks if tree changes, impossible to reuse, hidden dependency
var player = get_node("../../Player")
var ui = get_tree().get_root().get_node("Main/UI/HealthBar")
```

These are the #1 cause of "it worked then I refactored and everything broke."

---

## Node Tree Hierarchy Philosophy

Think of the scene tree in **relational terms**, not spatial terms. The question isn't "where is this node on screen?" but "does this node depend on its parent to exist?"

- If a node cannot function without its parent → it should be a child in that parent's scene
- If a node is independent → it can (and should) be its own scene instanced by the parent

The tree expresses **ownership**, not just rendering order.

```
Level (owns all of this)
├── Player (self-contained scene — works standalone)
├── Enemies (container)
│   ├── Goblin (self-contained scene — works standalone)
│   └── Goblin (same scene, different @export config)
├── UI (self-contained scene — reads from autoloads via signals)
└── Triggers (container for level-specific logic)
    ├── PressurePlate (self-contained — emits signal when stepped on)
    └── GateDoor (self-contained — opens when it hears the right signal)
```

---

## Project Folder Organization

Follow scene-first organization. Each scene gets its own folder containing itself and everything exclusive to it:

```
assets/
├── player/
│   ├── player.tscn
│   ├── player.gd
│   ├── player_sprite.png
│   └── states/
│       ├── idle.gd
│       └── run.gd
├── enemies/
│   ├── goblin/
│   │   ├── goblin.tscn
│   │   ├── goblin.gd
│   │   └── goblin_sprite.png
│   └── base_enemy.gd         ← shared base class lives with its "type"
├── ui/
│   ├── hud/
│   │   ├── hud.tscn
│   │   └── hud.gd
│   └── inventory_ui/
│       ├── inventory_ui.tscn
│       └── inventory_ui.gd
shaders/                       ← globally shared resources by type
audio/
addons/                        ← third-party only
```

Key rules:
- `snake_case` for all file and folder names (except `.cs` files which use PascalCase)
- Store globally shared resources in folders named after their type (`shaders/`, `audio/`, `fonts/`)
- Inherited scene folders nest inside their base scene's folder
- Third-party assets go in `addons/` with their licenses

---

## Scene Script Responsibilities

Each script type has a strict job. Crossing these boundaries is where debt accumulates.

| Script type | Its job | What it must NOT do |
|---|---|---|
| World object (door, lever, NPC) | Respond to interaction, emit signals, read GameState for conditions | Store game data, know about other world objects |
| Player script | Detect input, move, detect interactables, call `interact(self)` | Know what it's interacting with, store inventory/health |
| UI script | Read state via signals, display it, call manager methods on user action | Compute game logic, store game values, reach into world objects |
| Component (health bar, dialog box) | Receive data via method call, display it, emit UI events | Reach into game systems directly |
| Autoload/Manager | Own and mutate a domain of game state | Know about scene tree nodes directly |

---

## Composition Over Inheritance

Godot encourages composition through child nodes, not deep class hierarchies. Instead of `GoblinArcher extends Goblin extends Enemy`, prefer:

```
Enemy (base scene with core logic)
└── GoblinArcher (inherited scene that overrides specific nodes)
    ├── replaces: MeleeAttack with RangedAttack child scene
    └── sets @export values: different stats via inspector
```

Use inheritance when:
- A child scene *is* a variant of the parent (not just similar to it)
- You want to keep shared logic in one place and override specifics

Use composition (child scenes) when:
- You want to mix and match behaviors (an enemy that shoots AND charges → two component scenes)
- The behavior might appear on multiple different parent types

---

## Red Flags in Scene Design

**`get_parent()` or `../../` paths in a scene script** → use signals upward or @export injection

**A scene that works only in one specific level** → it has hidden environmental dependencies; extract them to @export

**A 500-line script on a scene** → the scene is doing too much; split into child scenes or delegate to autoloads

**Two scenes that reference each other** → circular dependency; introduce a parent or an EventBus event to mediate

**Nodes named "Manager" or "Controller" inside a scene** → these almost always belong as autoloads, not embedded nodes

**Scene that duplicates logic from an autoload** → delete the duplicate; the autoload is the single source of truth
