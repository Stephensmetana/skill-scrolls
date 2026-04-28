# GameState Conditions Reference

Load this file when: key/door puzzles, quest gates, flag-based conditions, locked areas, one-shot events.

---

## The Rule: World Objects Query GameState — They Never Inspect the Player

The door should never look at the player node to find out what they're carrying. The player node should never tell the door anything about its inventory. Instead, **both sides talk through GameState/InventoryManager**. The door asks if the condition is met; the manager knows because the inventory already updated it.

```
Pickup → InventoryManager.add_item(item)
           → InventoryManager.has_item("gold_key") now returns true

Door.interact(player) → asks InventoryManager.has_item("gold_key")
                      → if true: open()
                      → if false: play "locked" feedback
```

---

## Collecting a Key

The key (a world object) adds itself to the inventory when touched. It does not care who picks it up or what doors exist.

```gdscript
# KeyPickup.gd
extends Area2D

@export var item_data: ItemData  # assigned in inspector

func _on_body_entered(body):
    if body.is_in_group("player"):
        InventoryManager.add_item(item_data)
        queue_free()
```

## Checking the Condition at the Door

The door queries InventoryManager when the player interacts. It never receives the item — it just checks whether the condition is satisfied.

```gdscript
# LockedDoor.gd
@export var required_item_id: String = "gold_key"

func interact(_player):
    if InventoryManager.has_item(required_item_id):
        InventoryManager.remove_item(required_item_id)  # consume the key if desired
        open()
    else:
        _play_locked_feedback()

func open():
    # animate, disable collision, emit signal, etc.
    pass
```

---

## One-Shot Flags for Non-Item Conditions

For conditions that aren't inventory items (boss defeated, puzzle solved, NPC spoken to), store a flag in GameState:

```gdscript
# GameState.gd (autoload)
var flags: Dictionary = {}

func set_flag(flag_name: String) -> void:
    flags[flag_name] = true
    EventBus.flag_set.emit(flag_name)

func has_flag(flag_name: String) -> bool:
    return flags.get(flag_name, false)
```

```gdscript
# Boss.gd — on death
func _on_defeated():
    GameState.set_flag("boss_defeated")

# EscapeGate.gd
func interact(_player):
    if GameState.has_flag("boss_defeated"):
        open()
    else:
        _play_locked_feedback()
```

---

## Reacting to State Changes Globally

When a flag or inventory change should update UI or trigger world events, use EventBus so listeners don't need to poll:

```gdscript
# EventBus.gd
signal flag_set(flag_name: String)
signal inventory_changed

# QuestTracker UI
func _ready():
    EventBus.flag_set.connect(_on_flag_set)

func _on_flag_set(flag_name: String):
    if flag_name == "boss_defeated":
        _show_completion_banner()
```
