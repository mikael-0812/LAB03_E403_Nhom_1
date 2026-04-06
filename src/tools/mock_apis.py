import json
from typing import Dict, Any

def get_location() -> str:
    return "Quận 1, TP.HCM"

def search_cinema(movie: str, time: str) -> str:
    if "dune" in movie.lower() or "dune 2" == movie.lower():
        return f"Rạp CGV Vincom Center (Quận 1) có suất chiếu phim {movie} lúc 20:30, 21:45 hôm nay."
    return f"Không tìm thấy suất chiếu cho phim {movie} vào lúc {time}."

def check_inventory(item: str, radius: str) -> str:
    if "sữa" in item.lower():
        return f"Cửa hàng Circle K cách bạn 1km có sẵn {item}."
    return f"Không tìm thấy {item} trong bán kính {radius}."

def track_order(order_id: str) -> str:
    if "12345" in order_id:
        return "Đơn hàng #12345 đang được giao, dự kiến đến trong 15 phút nữa."
    return f"Đơn hàng #{order_id} đã được giao thành công."

def check_payment(order_id: str) -> str:
    if "99" in order_id:
        return "Error 500: Lỗi hệ thống khi kiểm tra trạng thái thanh toán."
    return f"Đơn hàng #{order_id} đã thanh toán thành công."

def escalate_to_human(reason: str) -> str:
    return f"Escalated to human agent successfully. Reason: {reason}. A support staff will assist the user shortly."

def search_restaurant(location: str, criteria: str) -> str:
    """Mock API to help with test case 4."""
    if "quận 1" in location.lower() and "chay" in criteria.lower():
        return "Tìm thấy quán chay 'Bông Súng' tại Quận 1, giá dưới 200k và đang mở cửa."
    return f"Không tìm thấy quán thỏa yêu cầu {criteria} ở {location}."

# Registry for easy mapping in agent
MOCK_API_FUNCTIONS = {
    "get_location": get_location,
    "search_cinema": search_cinema,
    "check_inventory": check_inventory,
    "track_order": track_order,
    "check_payment": check_payment,
    "escalate_to_human": escalate_to_human,
    "search_restaurant": search_restaurant
}

def execute_mock_tool(tool_name: str, args_str: str) -> str:
    """Parses JSON args and calls the function dynamically."""
    if tool_name not in MOCK_API_FUNCTIONS:
        return f"Error: Tool {tool_name} not found."
    
    func = MOCK_API_FUNCTIONS[tool_name]
    try:
        # If no args are expected and none given
        if not args_str or args_str.strip() == "" or args_str == "{}":
            return func()
            
        args = json.loads(args_str)
        return func(**args)
    except Exception as e:
        return f"Error calling tool {tool_name}: {str(e)}"

# Tools Schema for Agent Prompt
TOOLS_SCHEMA = [
    {
        "name": "get_location",
        "description": "Returns the current location of the user. No arguments required. Input empty string for arguments.",
        "parameters": {}
    },
    {
        "name": "search_cinema",
        "description": "Tìm kiếm rạp chiếu phim và lịch chiếu. Arguments (JSON): {\"movie\": \"tên phim\", \"time\": \"thời gian\"}",
        "parameters": {
            "type": "object",
            "properties": {
                "movie": {"type": "string"},
                "time": {"type": "string"}
            },
            "required": ["movie", "time"]
        }
    },
    {
        "name": "check_inventory",
        "description": "Kiểm tra hàng hóa trong bán kính cho trước. Arguments (JSON): {\"item\": \"tên món đồ\", \"radius\": \"bán kính\"}",
        "parameters": {
            "type": "object",
            "properties": {
                "item": {"type": "string"},
                "radius": {"type": "string"}
            },
            "required": ["item", "radius"]
        }
    },
    {
        "name": "track_order",
        "description": "Kiểm tra trạng thái đơn hàng. Arguments (JSON): {\"order_id\": \"Mã đơn hàng\"}",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"}
            },
            "required": ["order_id"]
        }
    },
    {
        "name": "check_payment",
        "description": "Kiểm tra thanh toán đơn hàng. Arguments (JSON): {\"order_id\": \"Mã đơn hàng\"}",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"}
            },
            "required": ["order_id"]
        }
    },
    {
        "name": "escalate_to_human",
        "description": "Chuyển cho nhân viên hỗ trợ khi có lỗi hoặc người dùng yêu cầu. Arguments (JSON): {\"reason\": \"Lý do chuyển\"}",
        "parameters": {
            "type": "object",
            "properties": {
                "reason": {"type": "string"}
            },
            "required": ["reason"]
        }
    },
    {
        "name": "search_restaurant",
        "description": "Tìm kiếm quán ăn dựa trên địa điểm và tiêu chí. Arguments (JSON): {\"location\": \"địa điểm\", \"criteria\": \"yêu cầu\"}",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string"},
                "criteria": {"type": "string"}
            },
            "required": ["location", "criteria"]
        }
    }
]
