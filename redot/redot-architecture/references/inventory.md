# Inventory System Reference

Load this file when: inventory features, item pickups, item-based conditions, shop systems.

Items are data. The inventory is a data store with logic. The UI is display only. These three layers must stay separate.

---

## Layer 1 — Item Data (Resource)

Each item is a `.tres` resource file. The resource path acts as a unique ID — no manual string ID management needed.

```gdscript
# item_data.gd
class_name ItemData
extends Resource

@export var item_name: String = ""
@export var description: String = ""
@export var icon: Texture2D
@export var stackable: bool = false
@export var max_stack: int = 1
```

Create item assets in the editor: right-click FileSystem → New Resource → ItemData → fill in inspector. Save as e.g. `res://items/gold_key.tres`, `res://items/health_potion.tres`.

---

## Layer 2 — InventoryManager (Autoload)

The InventoryManager is the single source of truth for what the player is carrying. All add/remove/query operations go through it. Nothing else stores inventory data.

```gdscript
# InventoryManager.gd (autoload)
extends Node

# Dictionary: ItemData resource → quantity
var _items: Dictionary = {}

func add_item(item: ItemData, amount: int = 1) -> void:
    _items[item] = _items.get(item, 0) + amount
    EventBus.inventory_changed.emit()

func remove_item(item: ItemData, amount: int = 1) -> bool:
    if not has_item_by_resource(item, amount):
        return false
    _items[item] -= amount
    if _items[item] <= 0:
        _items.erase(item)
    EventBus.inventory_changed.emit()
    return true

func has_item_by_resource(item: ItemData, amount: int = 1) -> bool:
    return _items.get(item, 0) >= amount

# Check by item_name string
func has_item(item_name: String, amount: int = 1) -> bool:
    for item in _items:
        if item.item_name == item_name:
            return _items[item] >= amount
    return false

# Remove by item_name string
func remove_item_by_name(item_name: String, amount: int = 1) -> bool:
    for item in _items:
        if item.item_name == item_name:
            return remove_item(item, amount)
    return false

func get_all_items() -> Dictionary:
    return _items.duplicate()

func clear() -> void:
    _items.clear()
    EventBus.inventory_changed.emit()
```

---

## Layer 3 — Inventory UI

The UI reads from InventoryManager and re-renders when it receives an `inventory_changed` signal. It never stores item data itself.

```gdscript
# InventoryUI.gd
const SLOT_SCENE = preload("res://ui/item_slot.tscn")

func _ready():
    EventBus.inventory_changed.connect(_refresh)
    _refresh()

func _refresh():
    for child in $SlotContainer.get_children():
        child.queue_free()

    for item in InventoryManager.get_all_items():
        var quantity = InventoryManager.get_all_items()[item]
        var slot = SLOT_SCENE.instantiate()
        slot.setup(item, quantity)
        $SlotContainer.add_child(slot)
```

---

## World Pickup → Inventory

A pickup item adds itself to the InventoryManager when touched. It does not know about the UI or any doors.

```gdscript
# ItemPickup.gd
extends Area2D

@export var item: ItemData

func _on_body_entered(body):
    if body.is_in_group("player"):
        InventoryManager.add_item(item)
        queue_free()
```

---

## Saving and Loading Inventory

Items are Resources, so store their resource paths in save data, not the objects themselves.

```gdscript
# In SaveManager.gd

func serialize_inventory() -> Dictionary:
    var data = {}
    for item in InventoryManager.get_all_items():
        data[item.resource_path] = InventoryManager.get_all_items()[item]
    return data

func deserialize_inventory(data: Dictionary) -> void:
    InventoryManager.clear()
    for path in data:
        var item = load(path) as ItemData
        if item:
            InventoryManager.add_item(item, data[path])
```

---

## Red Flags

- Player.gd contains an `items` array or dictionary → move to InventoryManager
- Door/chest checks `player.inventory.has("gold_key")` → query InventoryManager directly, never inspect the player node
- UI script calls remove logic conditionally → UI calls InventoryManager methods, but the *rules* for when to remove belong in the manager or GameState
- Item quantity stored in a UI slot node → slot displays quantity, InventoryManager owns it
- Deserializing a save without clearing first → always call `InventoryManager.clear()` before repopulating from a save
