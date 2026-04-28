---
name: redot-signals-eventbus
description: Redot 4 node/scene communication: signals, EventBus, callbacks. Triggers on "how does X know about Y", "how does UI know when health changes", cross-scene or cross-system communication. Also trigger on get_parent(), get_node("../../"), or sibling-to-sibling direct calls in generated code.
---

# Redot Signals & EventBus Guide

Communication between nodes and scenes is where most LLM-generated code goes wrong. The pattern is simple but must be applied consistently: **Call Down, Signal Up, EventBus Across**.

This skill covers the three communication tiers and when to use each. For scene design decisions, use `redot-scene-design`. For system/autoload architecture, use `redot-architecture`.

---

## The Three Communication Tiers

### Tier 1: Direct Calls (Parent → Child)

A parent knows its children. It can call their methods and read their properties directly.

```gdscript
# Level.gd — parent calling down to its children: CORRECT
func _ready():
    $Player.set_spawn_point(spawn_position)
    $HUD.set_level_name(level_name)
```

Use `$ChildName` or `get_node("ChildName")` (one level only — never `../../`).

### Tier 2: Signals (Child → Parent, or Any Node → Ancestor)

A child never calls up the tree. When something happens in a child that its parent needs to know about, the child emits a signal. The parent (or a common ancestor) connects to it.

```gdscript
# Player.gd — child emitting upward: CORRECT
signal health_changed(new_health: int)
signal died

var health := 100:
    set(value):
        health = value
        health_changed.emit(health)
        if health <= 0:
            died.emit()
```

```gdscript
# Level.gd — parent listening to child: CORRECT
func _ready():
    $Player.died.connect(_on_player_died)
    $Player.health_changed.connect($HUD.update_health)
```

**The parent is the wiring layer.** It connects its children to each other. The children themselves know nothing about each other.

### Tier 3: EventBus (Cross-Scene, Cross-System)

When two nodes are in different scenes with no common parent that can wire them up, use the EventBus autoload — a global signal bus. No direct references needed; anything in the game can emit or listen.

```gdscript
# EventBus.gd (Autoload — signals only, zero logic, zero state)
extends Node

signal player_health_changed(new_health: int)
signal player_died
signal item_picked_up(item: ItemData)
signal enemy_defeated(enemy_id: String)
signal game_paused
signal game_unpaused
```

```gdscript
# Player.gd — emits to the bus, not directly to UI
var health := 100:
    set(value):
        health = value
        EventBus.player_health_changed.emit(health)
```

```gdscript
# HUD.gd — listens on the bus, no reference to Player needed
func _ready():
    EventBus.player_health_changed.connect(_on_health_changed)

func _on_health_changed(new_health: int):
    $HealthBar.value = new_health
```

---

## Choosing the Right Tier

| Situation | Use |
|---|---|
| Parent configuring a child on startup | Direct call / @export |
| Parent responding to child event | Signal (connect in parent's `_ready`) |
| Sibling A telling sibling B something | Signal up to parent → parent calls down to B |
| Two nodes in different scenes | EventBus signal |
| UI updating when game state changes | EventBus signal |
| World object triggering another world object (same scene) | Signal, wired in parent |
| World object triggering another world object (different scene) | EventBus with ID matching |

**When in doubt, prefer EventBus.** The cost is a small amount of indirection. The benefit is that neither side knows the other exists, which makes both easier to change, test, and reuse.

---

## Signal Design Rules

### Define signals at the top of the script
```gdscript
class_name Enemy
extends CharacterBody2D

signal defeated(enemy_id: String)
signal health_changed(new_health: int)
signal attack_started
```

Signals defined at the top are the script's public contract — they tell you everything this object can communicate outward.

### Use typed parameters
```gdscript
# BAD — caller doesn't know what's in the signal
signal item_collected(data)

# GOOD — explicit, autocomplete works, errors surface earlier
signal item_collected(item: ItemData, quantity: int)
```

### Don't bubble signals more than once
If you're re-emitting a child's signal from a parent, and then re-emitting again from the grandparent, something is wrong with the scene structure. Consider whether you should be using EventBus instead, or whether the scene tree needs to be flattened.

```gdscript
# BAD — signal chain that's hard to trace
# Health → Player → Level → Game → UI
# Every layer re-emits the one below it

# GOOD — emit once on EventBus, UI listens directly
# Health emits → EventBus.player_health_changed → UI updates
```

### Keep EventBus signals small
If a signal carries more than 3 parameters, ask whether the receiver should be calling a GameState helper instead of receiving all that data. Overstuffed signals couple the emitter and receiver together almost as tightly as a direct reference.

```gdscript
# BAD — receiver knows everything about the source
signal combat_result(attacker, defender, damage, crit, status_effect, new_health, ...)

# GOOD — receiver fetches what it needs from GameState
signal combat_result(attacker_id: String, defender_id: String)
# Receiver: GameState.get_combatant(attacker_id).health, etc.
```

---

## The EventBus as Interface Contract

Think of EventBus like a typed API surface — a set of contracts the game systems communicate through. Designing it explicitly prevents spaghetti:

1. **Group signals by domain**
```gdscript
# EventBus.gd
extends Node

# --- Player ---
signal player_health_changed(new_health: int)
signal player_died
signal player_leveled_up(new_level: int)

# --- Inventory ---
signal inventory_changed
signal item_equipped(item: ItemData)

# --- World ---
signal world_trigger(target_id: String)
signal checkpoint_reached(checkpoint_id: String)

# --- UI ---
signal dialog_started(dialog_id: String)
signal dialog_ended
```

2. **Zero logic, zero state on EventBus.** It's a relay, not a manager. If you find yourself adding `if` statements or variables to EventBus, move that logic to a domain manager autoload.

3. **Connect in `_ready()`, disconnect in `_exit_tree()` when needed**
```gdscript
func _ready():
    EventBus.player_health_changed.connect(_on_health_changed)

func _exit_tree():
    EventBus.player_health_changed.disconnect(_on_health_changed)
```

For nodes that are instanced and freed frequently (enemies, projectiles), always disconnect to avoid calling methods on freed objects.

---

## Common Patterns with Code Examples

### Pattern: UI Health Bar

```gdscript
# Player.gd
signal health_changed(new_health: int)

var _health: int = 100

func take_damage(amount: int) -> void:
    _health = max(0, _health - amount)
    EventBus.player_health_changed.emit(_health)
    if _health == 0:
        EventBus.player_died.emit()
```

```gdscript
# HealthBar.gd
func _ready():
    EventBus.player_health_changed.connect(_on_health_changed)

func _on_health_changed(new_health: int):
    $Bar.value = new_health
    $Label.text = str(new_health)
```

Neither script references the other. Either can be replaced without touching the other.

### Pattern: Wiring Siblings via Parent

```gdscript
# Level.gd — owns both PressurePlate and Gate
func _ready():
    $PressurePlate.activated.connect($Gate.open)
    $PressurePlate.deactivated.connect($Gate.close)
```

```gdscript
# PressurePlate.gd — knows nothing about Gate
signal activated
signal deactivated

func _on_body_entered(_body):
    activated.emit()

func _on_body_exited(_body):
    deactivated.emit()
```

```gdscript
# Gate.gd — knows nothing about PressurePlate
func open() -> void:
    # animate open
    pass

func close() -> void:
    # animate close
    pass
```

### Pattern: Cross-Scene World Triggers (EventBus + ID)

```gdscript
# EventBus.gd
signal world_trigger(target_id: String)
```

```gdscript
# Lever.gd
@export var target_id: String = ""

func interact(_player) -> void:
    EventBus.world_trigger.emit(target_id)
```

```gdscript
# Door.gd
@export var my_id: String = ""

func _ready():
    EventBus.world_trigger.connect(_on_world_trigger)

func _on_world_trigger(id: String) -> void:
    if id == my_id:
        _open()
```

Designers set `target_id` on the lever and `my_id` on the door in the Inspector. No code changes needed to wire new triggers to new doors.

---

## Anti-Patterns to Refuse

**`get_parent()` in a child script**
→ The child is assuming a specific parent type. Use signals upward instead.

**`get_node("../../SomeDistantNode")`**
→ Fragile path that breaks on any tree change. Use EventBus or @export injection.

**Two scenes that hold direct references to each other**
→ Circular dependency. Introduce a mediator (parent or EventBus).

**Connecting signals across 4+ hops (bubbling)**
→ Flatten with EventBus. More than 2 re-emissions to track a connection is too many.

**Logic inside EventBus.gd**
→ EventBus is signals only. Move logic to domain managers.

**Connecting to a freed node's method**
→ Always `disconnect()` in `_exit_tree()` for nodes that get freed. Or use `connect(..., CONNECT_ONE_SHOT)` for one-time events.
