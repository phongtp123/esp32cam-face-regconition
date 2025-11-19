import numpy as np

def process_image_data(img: np.ndarray):
    
    height, width = img.shape
    
    # Chuẩn hóa ảnh về [0,1]
    normalized = img.astype(np.float64) / 255.0

    # Khởi tạo ma trận tích phân có padding 0
    integral_matrix = np.zeros((height + 1, width + 1), dtype=np.float64)
    squared_integral_matrix = np.zeros((height + 1, width + 1), dtype=np.float64)

    # Tính integral và squared integral theo công thức tích lũy
    for y in range(height):
        for x in range(width):
            value = normalized[y, x]
            integral_matrix[y + 1, x + 1] = (
                value
                + integral_matrix[y, x + 1]
                + integral_matrix[y + 1, x]
                - integral_matrix[y, x]
            )
            squared_integral_matrix[y + 1, x + 1] = (
                value * value
                + squared_integral_matrix[y, x + 1]
                + squared_integral_matrix[y + 1, x]
                - squared_integral_matrix[y, x]
            )

    return integral_matrix, squared_integral_matrix

def rect_sum(matrix: np.ndarray, x, y, w, h): 
    x, y, w, h = int(x), int(y), int(w), int(h)
    return matrix[y + h, x + w] - (matrix[y + h, x] if (x > 0) else 0) - (matrix[y, x + w] if (y > 0) else 0) + (matrix[y, x] if (x > 0 and y > 0) else 0)
