---
name: redot-llm-codegen
description: Redot 4 GDScript code generation enforcement. Triggers on "write code for X", "implement Y", "add Z feature", "generate script for", "make scene that does". Apply before writing any GDScript — enforces prohibited/required patterns.
---

# Redot LLM Code Generation Rules

This skill exists because LLMs default to patterns that work in demos but create tech debt in real games. The patterns below are **hard rules** — not suggestions. Deviate only when the constraint genuinely doesn't apply and you can state why.

Before writing any GDScript, read through the prohibited patterns list. Then apply the required patterns in your output.

---

## Prohibited Patterns — Never Generate These

### ❌ Hardcoded node paths with traversal
```gdscript
# NEVER generate any of these
get_node("../../Player")
get_parent().get_parent().get_node("UI")
get_tree().get_root().get_node("Main/HUD/HealthBar")
$"../SomeNode"
```
**Replace with:** `@export` variables, EventBus signals, or parent-wired signal connections.

### ❌ Sibling-to-sibling direct calls from within a script
```gdscript
# NEVER generate this in Sibling_A.gd
func _ready():
    get_parent().get_node("SiblingB").do_something()
```
**Replace with:** Sibling A emits a signal. The common parent connects that signal to Sibling B's method in the parent's `_ready()`.

### ❌ Game logic in UI scripts
```gdscript
# NEVER put logic like this in a UI script
func _on_buy_button_pressed():
    if player.gold >= item.cost and player.inventory.size() < 20:
        player.gold -= item.cost
        player.inventory.append(item)
        update_display()
```
**Replace with:** UI calls a manager method. The manager decides if the action is valid and handles all state changes.
```gdscript
# CORRECT — UI calls manager, manager enforces rules
func _on_buy_button_pressed():
    ShopManager.purchase(current_item)
    # UI updates via EventBus signal emitted by ShopManager
```

### ❌ State stored in world objects or UI nodes
```gdscript
# NEVER store persistent game data here
class_name Chest extends Node3D
var has_been_opened: bool = false  # ← this dies when the scene unloads
var contained_item: ItemData       # ← same problem
```
**Replace with:** World objects read their state from GameState using their ID. They don't own it.
```gdscript
class_name Chest extends Node3D
@export var chest_id: String = ""

func interact(_player) -> void:
    if not GameState.is_chest_opened(chest_id):
        GameState.open_chest(chest_id)  # state lives in GameState
        EventBus.chest_opened.emit(chest_id)
```

### ❌ Loading another script to call a helper
```gdscript
# NEVER do this
var helper = load("res://scripts/some_world_object.gd").new()
var result = helper.calculate_something()
```
**Replace with:** Move the helper to a shared autoload. `SomeManager.calculate_something()`.

### ❌ Children calling get_parent() for logic
```gdscript
# NEVER do this in a child script
func take_damage(amount):
    health -= amount
    if health <= 0:
        get_parent().on_child_died(self)  # child shouldn't know its parent type
```
**Replace with:** Child emits a signal. Parent listens.
```gdscript
signal died

func take_damage(amount: int) -> void:
    health -= amount
    if health <= 0:
        died.emit()
```

### ❌ Player node holding inventory, quests, or global flags
```gdscript
# NEVER store these on Player
class_name Player extends CharacterBody2D
var inventory: Array = []
var gold: int = 0
var quests_completed: Array = []
var has_visited_town: bool = false
```
**Replace with:** Player owns only locomotion and input state. Persistent data lives in dedicated managers.

---

## Required Patterns — Always Generate These

### ✅ @export for inspector-configurable values
Any value a designer might want to tune, or any node reference a scene needs from outside, uses `@export`:
```gdscript
@export var speed: float = 200.0
@export var required_key: ItemData
@export var target_id: String = ""
@export var spawn_delay: float = 1.0
```

### ✅ Signals defined at the top of every script that emits events
```gdscript
class_name Enemy extends CharacterBody2D

signal defeated(enemy_id: String)
signal health_changed(new_health: int)
signal attack_started(target: Node)
```

### ✅ Typed parameters on signals
```gdscript
# BAD
signal item_collected(data)

# GOOD
signal item_collected(item: ItemData, quantity: int)
```

### ✅ Type hints everywhere
```gdscript
# BAD
var speed = 200
func move(direction):

# GOOD
var speed: float = 200.0
func move(direction: Vector2) -> void:
```

### ✅ Setter methods for state that emits signals
```gdscript
var _health: int = 100

func take_damage(amount: int) -> void:
    _health = max(0, _health - amount)
    EventBus.player_health_changed.emit(_health)
    if _health == 0:
        EventBus.player_died.emit()

func heal(amount: int) -> void:
    _health = min(max_health, _health + amount)
    EventBus.player_health_changed.emit(_health)
```
Never expose raw setters on health, gold, or any value that should trigger downstream reactions. Wrap in methods.

### ✅ Parent wires children in _ready()
```gdscript
# Level.gd — the wiring layer
func _ready():
    $PressurePlate.activated.connect($Door.open)
    $Player.died.connect(_on_player_died)
    $Player.health_changed.connect($HUD.update_health)
```

### ✅ Cross-scene communication via EventBus + ID
```gdscript
# Triggering side
@export var target_id: String = ""
EventBus.world_trigger.emit(target_id)

# Receiving side
@export var my_id: String = ""
func _ready():
    EventBus.world_trigger.connect(_on_world_trigger)

func _on_world_trigger(id: String) -> void:
    if id == my_id:
        _activate()
```

### ✅ Group membership for world object queries
```gdscript
# PREFER for world objects — decouples from Player class
if body.is_in_group("player"):

# OK when you need static type checking
if body is Player:
```

### ✅ call_deferred() when modifying the scene tree from physics/process callbacks
```gdscript
func _on_body_entered(body):
    if body.is_in_group("player"):
        queue_free.call_deferred()  # never free self during a physics callback
```

---

## Scene Scaffolding Template

When generating a new scene script, follow this structure:

```gdscript
class_name MyThing
extends Node2D  # or appropriate base type

# ── Signals ──────────────────────────────────────────────
signal something_happened(data: String)

# ── Exports (inspector-configurable) ─────────────────────
@export var some_value: float = 1.0
@export var some_resource: SomeResource

# ── Constants ─────────────────────────────────────────────
const MAX_VALUE: int = 100

# ── Private state (no public access to mutable vars) ──────
var _internal_counter: int = 0
var _is_active: bool = false

# ── Lifecycle ─────────────────────────────────────────────
func _ready() -> void:
    # Connect to EventBus if needed
    # DO NOT reach into siblings or parents here
    pass

func _process(delta: float) -> void:
    # Keep thin — delegate to private methods
    pass

# ── Public API (what parents and managers call) ────────────
func activate() -> void:
    _is_active = true
    _do_the_thing()

# ── Signal handlers ────────────────────────────────────────
func _on_some_event(data: String) -> void:
    pass

# ── Private implementation ─────────────────────────────────
func _do_the_thing() -> void:
    something_happened.emit("done")
```

---

## Autoload Scaffolding Template

When generating a new manager autoload:

```gdscript
# MyManager.gd (Project Settings → AutoLoad)
extends Node

# ── State (this manager is the single source of truth) ────
var _data: Dictionary = {}

# ── Public API ─────────────────────────────────────────────
func do_something(input: SomeType) -> bool:
    if not _is_valid(input):
        return false
    _apply(input)
    EventBus.something_changed.emit()
    return true

func get_value(key: String) -> Variant:
    return _data.get(key, null)

# ── Private ────────────────────────────────────────────────
func _is_valid(input: SomeType) -> bool:
    return input != null

func _apply(input: SomeType) -> void:
    _data[input.id] = input
```

---

## Pre-Generation Checklist

Before writing the first line of code for any feature:

- [ ] Where does new state live? (GameState, a domain manager, or inside a scene that owns it exclusively)
- [ ] What signals need to exist on EventBus for this feature?
- [ ] Does any world object need an `@export var my_id: String` for cross-scene linking?
- [ ] Is the UI reading from EventBus and calling managers — not computing or storing anything?
- [ ] Will SaveManager need to be updated with new serialization/deserialization?
- [ ] Do any new nodes get freed at runtime? If so, do they disconnect from EventBus in `_exit_tree()`?
