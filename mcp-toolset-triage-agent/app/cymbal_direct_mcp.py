from fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("CymbalLogistics")

# Mock Databases
ORDERS = {
    "CYM-EC-9921": {
        "customer_id": "CUST-7742",
        "status": "DELAYED",
        "reason": "Severe winter storm at East Coast fulfillment center."
    },
    "CYM-EC-1001": {
        "customer_id": "CUST-1001",
        "status": "DELIVERED",
        "reason": ""
    },
    "CYM-EC-1002": {
        "customer_id": "CUST-1002",
        "status": "DELAYED",
        "reason": "Severe winter storm at East Coast fulfillment center."
    },
    "CYM-EC-1003": {
        "customer_id": "CUST-1003",
        "status": "DELAYED",
        "reason": "Severe winter storm at East Coast fulfillment center."
    },
    "CYM-EC-1004": {
        "customer_id": "CUST-1004",
        "status": "DELAYED",
        "reason": "Severe winter storm at East Coast fulfillment center."
    }
}

CUSTOMERS = {
    "CUST-7742": {
        "name": "Jane Doe",
        "tier": "GOLD"
    },
    "CUST-1001": {
        "name": "John Smith",
        "tier": "MEMBER"
    },
    "CUST-1002": {
        "name": "Alice Johnson",
        "tier": "PLATINUM"
    },
    "CUST-1003": {
        "name": "Bob Williams",
        "tier": "SILVER"
    },
    "CUST-1004": {
        "name": "Charlie Brown",
        "tier": "MEMBER"
    }
}

# In-memory record of compensations issued
COMPENSATIONS = []

@mcp.tool()
def get_order_status(order_id: str) -> str:
    """Get the status of a Cymbal Direct order and any delay reasons."""
    order = ORDERS.get(order_id)
    if not order:
        return f"Order {order_id} not found."
    
    return f"Order {order_id} is {order['status']}. Reason: {order['reason']}. Customer ID: {order['customer_id']}"

@mcp.tool()
def get_customer_loyalty_info(customer_id: str) -> str:
    """Get the loyalty tier for a Cymbal Direct customer. Returns tier (MEMBER, SILVER, GOLD, PLATINUM)."""
    customer = CUSTOMERS.get(customer_id)
    if not customer:
        return f"Customer {customer_id} not found."
    
    return f"Customer {customer_id} is in the {customer['tier']} tier."

@mcp.tool()
def issue_disruption_compensation(customer_id: str, compensation_amount: str, shipping_upgrade: str) -> str:
    """Issue compensation and shipping upgrades to a customer affected by a disruption."""
    if customer_id not in CUSTOMERS:
        return f"Error: Customer {customer_id} not found."
    
    record = {
        "customer_id": customer_id,
        "compensation_amount": compensation_amount,
        "shipping_upgrade": shipping_upgrade
    }
    COMPENSATIONS.append(record)
    return f"Successfully issued {compensation_amount} credit and {shipping_upgrade} shipping upgrade to {customer_id}."

if __name__ == "__main__":
    mcp.run(transport='stdio')
