# App Constants

from enums import MessageType, OpStatus

RESPONSE = {
    MessageType.order_create: {
        OpStatus.create_ok: "Order created successfully with id: {id}, name: {name}",
        OpStatus.create_failed: "Order create failed",
        OpStatus.update_ok: "Order updated successfully",
        OpStatus.update_failed: "Order update failed",
    },
    MessageType.order_delete: {
        OpStatus.delete_ok: "Order deleted successfully",
        OpStatus.delete_failed: "Order delete failed",
    }
}