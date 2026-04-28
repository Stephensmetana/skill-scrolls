---
name: redot-architecture
description: Redot 4 GDScript system design. Triggers on adding new systems, planning multi-script features, "add X to game", "implement Y", "how should I structure Z", "plan out W". Covers autoload responsibilities, GameState/SaveManager/InventoryManager patterns, interaction system architecture, cross-scene wiring decisions.
---

# Redot Architecture Guide

This skill ensures good architectural decisions in Redot 4 GDScript games. Apply it during planning — before writing any code — and use it to check implementation decisions as you go.

The goal is to prevent the most common failure mode in AI-assisted game dev: features that work in isolation but break other parts of the game when added, because they reach into the wrong systems or bypass established patterns.

---

## Before Writing Any Code — Ask These Four Questions

**1. Where does the data live?**
Game state belongs in one place. If you are about to store something new, decide: does it go in the existing state singleton, or does it belong to a specific scene? Data that multiple systems need (health, inventory, flags, score) → singleton. Data that only one scene needs (animation frame, local timer) → that scene's script.

Never store the same data in two places. If you find yourself syncing variables between scripts, that is a sign the data is in the wrong place.

**2. Who owns the logic?**
- Rules about how the game works → GameState or a dedicated system autoload
- Rules about how things look → UI scripts only
- Coordination between systems → a central manager or tick autoload

UI scripts must not contain game logic. If a UI script is checking a win condition, computing a value, or modifying state directly, that logic belongs in GameState instead. UI reads state and displays it. UI does not compute it.

**3. How do systems talk to each other?**
Use EventBus signals for cross-system communication. Never have two scripts call each other directly unless one clearly owns the other (parent calls child is fine; sibling calls sibling is a red flag; child calling parent is almost always wrong).

The correct pattern:
- Something happens in the game → a system or world object emits a signal on EventBus (or calls GameState directly)
- UI listens on EventBus and updates itself
- UI actions call methods on GameState directly (one direction only)

If you are about to write `get_node("../../SomeOtherNode")` or load another script just to call a function, stop. Use EventBus instead or move the logic to a shared autoload.

**4. Will SaveManager break?**
Any new field added to GameState must be handled in SaveManager. Before adding a field, check: is it serialized? Is it restored? If the game loads a save that predates this field, does it degrade gracefully with a default value?

---

## Architecture Patterns to Follow

### Autoload Responsibilities
These are the standard autoloads for most games. Not every game needs all of them — add only what your game requires. Keep these boundaries strict.

| Autoload | Owns |
|----------|------|
| Constants | All static data (item definitions, tuning values). Never mutated at runtime. |
| GameState | All mutable runtime state + helper/query methods |
| EventBus | Signal definitions only. No logic, no state. |
| SaveManager | Serialize/deserialize GameState. Nothing else. |
| InventoryManager | Item storage, add/remove/query logic. Emits signals on change. |
| Domain-specific managers | e.g. QuestManager, CombatManager, AudioManager — one focused domain each |

Only create a new autoload when a concern is truly global and needs to persist across scenes. A mechanic that only exists in one level belongs in that level's script, not in an autoload.

### Scene / Script Responsibilities
World object scripts (doors, levers, chests, NPCs): respond to being interacted with, emit signals, read from GameState for conditions. They do not store game data.

UI scripts: read GameState via EventBus signals, display results, call GameState methods on user input. They do not compute game values.

Component scripts (dialogs, overlays, HUD elements): receive data via method calls or signals, display it, emit results. Do not reach into game systems directly.

### The Helper Problem
Never load another script just to call a helper function. If multiple scripts need the same helper, it belongs in a shared autoload — not in a single world script that other scripts then depend on. A script that is both a consumer and a dependency of others creates circular coupling.

---

## Scene Tree Communication

**Call Down, Signal Up, EventBus Across.** For the full signal/EventBus pattern guide and code examples, see `redot-signals-eventbus`. Short rules:
- Parent → child: direct call (`$Child.method()`)
- Child → parent/ancestor: emit a signal; parent connects in `_ready()`
- Cross-scene: EventBus autoload with string IDs, never direct node references

---

## Interaction System Architecture

Use this pattern whenever the player can interact with world objects (buttons, doors, levers, NPCs, pickups, etc.).

### The Core Rule: Player Stays Dumb
The player never knows what it is interacting with. It only does three things:
1. **Detects** nearby interactables via an Area2D/3D overlap
2. **Tracks** which one is the current target
3. **Broadcasts** the interact input by calling `interact(self)` on the target

```gdscript
# Player.gd
var current_interactable = null

func _on_interact_area_body_entered(body):
    if body.has_method("interact"):
        current_interactable = body

func _on_interact_area_body_exited(body):
    if current_interactable == body:
        current_interactable = null

func _unhandled_input(event):
    if event.is_action_pressed("interact") and current_interactable:
        current_interactable.interact(self)
```

`has_method("interact")` is Godot's duck-typing pattern — it works as an interface contract without needing a shared base class. Area2D/3D overlaps work the same way; swap `body` for `area` if your interactables use Area nodes.

### Interactable Objects Own Their Logic
Each interactable decides what happens internally. The player passes itself as context (so the interactable can read from it if needed), but the object is in charge.

```gdscript
# Lever.gd
signal activated

func interact(_player):
    activated.emit()
    _play_animation()
```

### Button → Door (Same Scene)
Wire them in their common parent. Neither object references the other.

```gdscript
# Level.gd
func _ready():
    $Lever.activated.connect($BridgeDoor.open)
```

### Base Class Pattern (for many interactable types)
When you have many kinds of interactables, use a shared base class:

```gdscript
# interactable.gd
class_name Interactable
extends Area2D  # or Area3D, or StaticBody2D — whatever fits

signal interacted

func interact(interactor) -> void:
    interacted.emit()
    _on_interact(interactor)

func _on_interact(_interactor) -> void:
    pass  # override in subclass

func get_prompt() -> String:
    return "Interact"  # override for context-sensitive prompts
```

Subclasses override `_on_interact()` to implement specific behaviour. The player calls `interact()` on all of them identically.

### Interaction Detection: Area vs Raycast
- **Area2D/3D overlap**: best for 2D games or 3D games with a generous interaction radius
- **RayCast3D**: best for first-person games where the player looks at objects

```gdscript
# First-person raycast version
func _unhandled_input(event):
    if event.is_action_pressed("interact"):
        var hit = $RayCast3D.get_collider()
        if hit and hit.has_method("interact"):
            hit.interact(self)
```

### Interaction System Red Flags
- Player script contains `if interactable is Door:` type-checking → the interactable should handle its own logic
- Object holds `@export var other_object: NodePath` to a sibling → use parent wiring or EventBus IDs instead
- `get_parent().get_parent().do_thing()` anywhere → signals or EventBus instead
- Interactable listens for the interact key itself → only the player reads input; it calls the interactable

---

## Reference Files (load on demand)

- `./references/conditions.md` — Load for key/door puzzles, quest gates, flag-based conditions, one-shot events. Core rule: world objects query GameState/InventoryManager; they never inspect the player node.
- `./references/inventory.md` — Load for inventory features, item pickups, item-based conditions, shop systems. Core rule: ItemData resources are the item type; InventoryManager autoload is the single source of truth; UI reads via EventBus signals.

---

## Before Implementing — Check This List

Go through this before writing the first line of code for any new feature:

- [ ] New data fields: added to GameState or InventoryManager, added to SaveManager serialize, added to SaveManager deserialize with a fallback default
- [ ] New logic: lives in GameState or a domain manager autoload, not in a world script or UI script
- [ ] New UI: reads state via EventBus signals, does not compute or store game values itself
- [ ] Cross-system communication: uses EventBus signals or direct calls to autoloads — not direct node references or script loads
- [ ] World condition checks (locked doors, quest gates): query GameState/InventoryManager — never inspect the player node
- [ ] New items: defined as ItemData resources, assigned via @export in the inspector
- [ ] Save compatibility: new fields have fallback defaults in the deserialize step

---

## Red Flags — Stop and Reconsider

**Duplicated logic:** The same rule checked in more than one place. When the rule changes, one copy gets updated and the other doesn't. Consolidate to GameState.

**UI script doing math or checking conditions:** Move to GameState and expose a helper method. The UI calls the helper and displays the result.

**Direct script loading for helpers:** `load("res://scripts/some_other.gd")` from inside another script just to call a function. Create a shared autoload instead.

**Two scripts that both read and write the same variable:** Whoever writes last wins. This causes state drift. One script owns the variable; others read it or request changes through the owner.

**World object inspecting the player node:** `player.inventory`, `player.has_key`, `player.health` — these reach into the player and couple the world to its internals. Query GameState or InventoryManager instead.

**New save fields without migration:** A new field in GameState that SaveManager doesn't know about will silently be null on load for any existing save. Always add a fallback default in the deserialize step.

**Signals with too many parameters:** If an EventBus signal carries more than 2–3 parameters, consider whether you're overcoupling two systems. Often the receiver should call a GameState helper instead of receiving all that data through a signal.

---

## How to Add a New Feature Correctly

Use this sequence every time:

1. **Define the data.** What new state does this feature need? Add it to GameState or the appropriate domain manager with sensible defaults. Update SaveManager immediately.

2. **Define the logic.** What rules govern this feature? Write them as methods on GameState or a domain autoload. Keep them pure where possible.

3. **Define the signals.** Does the rest of the game need to know when this feature changes something? Add the minimum necessary signals to EventBus.

4. **Wire the world objects.** Build pickups, doors, triggers, and other world objects. They read from GameState for conditions and emit signals upward.

5. **Wire the UI last.** Build UI after the logic exists. The UI should be thin: it reads state, displays it, and calls manager methods on user input.

This order matters. UI built before logic exists tends to smuggle logic into the UI script, because it is the easiest place to put it at the time.

---

## Redot-Specific Notes

- Prefer `@export` variables for values that need tuning in the inspector; it avoids magic numbers buried in logic
- Use `signal` definitions at the top of scripts that emit events; makes the contract explicit
- `call_deferred()` when modifying scene tree from within a physics or process callback to avoid frame conflicts
- Autoloads are always available without `get_node()` — use them directly by name
- `preload()` for assets you always need; `load()` only for conditional/dynamic loads
- Keep `_process()` and `_physics_process()` as thin as possible — delegate to methods with clear names
- Use `is_in_group("player")` instead of `body is Player` — it keeps world objects decoupled from the Player class
