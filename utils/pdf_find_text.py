import fitz
import traceback
import os
import cv2

def find_text_with_coords_per_char(pdf_doc, search_text, dpi=300):
    scale = dpi / 72  # DPI转换比例
    found_positions = []
    global_line_number = 1  # 全局行号从1开始
    
    for page_num in range(len(pdf_doc)):
        page = pdf_doc.load_page(page_num)
        text_instances = page.get_text("dict")['blocks']
        spans = []
        
        for block in text_instances:
            if block['type'] == 0:
                for line in block['lines']:
                    for span in line['spans']:
                        for i, char in enumerate(span["text"]):
                            char_width = (span["bbox"][2] - span["bbox"][0]) / len(span["text"])
                            char_x0 = span["bbox"][0] + i * char_width
                            char_x1 = char_x0 + char_width
                            spans.append({
                                "char": char,
                                "bbox": (char_x0, span["bbox"][1], char_x1, span["bbox"][3]),
                                "index": len(spans),
                                "page": page_num + 1,
                                "line_number": global_line_number,
                                "char_index": i,
                            })
                    global_line_number += 1
        
        i = 0
        while i < len(spans):
            if spans[i]["char"] == search_text[0]:
                current_text = spans[i]["char"]
                matched_spans = [spans[i]]
                j = i + 1
                for t_idx in range(1, len(search_text)):
                    if j < len(spans) and spans[j]["char"] == search_text[t_idx]:
                        current_text += spans[j]["char"]
                        matched_spans.append(spans[j])
                        j += 1
                    else:
                        break
                if current_text == search_text:
                    for span in matched_spans:
                        pixel_coords = (
                            span["bbox"][0] * scale, span["bbox"][1] * scale,
                            span["bbox"][2] * scale, span["bbox"][3] * scale
                        )
                        found_positions.append({
                            "page": span["page"],
                            "text": span["char"],
                            "line_number": span["line_number"],
                            "char_index": span["char_index"],
                            "pdf_bbox": span["bbox"],
                            "pixel_bbox": pixel_coords,
                        })
                i = j
            else:
                i += 1
    
    line_coords = {}
    for result in found_positions:
        line_number = result['line_number']
        if line_number not in line_coords:
            line_coords[line_number] = {
                'line_text': '',
                'min_x': float('inf'),
                'max_x': float('-inf'),
                'y0': result['pdf_bbox'][1],
                'y1': result['pdf_bbox'][3],
                'page': result['page'],
            }
        line_coords[line_number]['line_text'] += result['text']
        line_coords[line_number]['min_x'] = min(line_coords[line_number]['min_x'], result['pdf_bbox'][0])
        line_coords[line_number]['max_x'] = max(line_coords[line_number]['max_x'], result['pdf_bbox'][2])
    
    response_data = []
    for line_number, data in line_coords.items():
        page = pdf_doc.load_page(data['page'] - 1)
        text_instances = page.search_for(data['line_text'])
        
        for x0, y0, x1, y1 in text_instances:
            if search_text != data['line_text']:
                continue
            response_data.append({
                "page": data['page'],
                "text": data['line_text'],
                "start_pixel": (x0 * scale, y0 * scale),
                "end_pixel": (x1 * scale, y1 * scale)
            })
    
    return response_data

def find_text_in_pdf(pdf_doc, search_text, dpi=300):
    found_positions = []
    
    for page_num in range(len(pdf_doc)):
        page = pdf_doc.load_page(page_num)
        text_instances = page.search_for(search_text)
        
        for rect in text_instances:
            x0, y0, x1, y1 = rect
            found_positions.append({
                "page": page_num + 1,
                "text": search_text,
                "start_pixel": (x0 * (dpi / 72), y0 * (dpi / 72)),# 左上角
                "end_pixel": (x1 * (dpi / 72), y1 * (dpi / 72))
            })
    
    return found_positions

def find_partial_text_and_continue(pdf_doc, full_text):
    all_found_positions = []
    
    while True:
        if full_text:
            positions = find_text_in_pdf(pdf_doc, full_text)
            if len(positions) > 0:
                all_found_positions.extend(positions)
                full_text = ""
            else:
                remaining_text = full_text
                while True:
                    remaining_text = remaining_text[:-1]
                    positions = find_text_in_pdf(pdf_doc, remaining_text)
                    if len(positions) > 0:
                        all_found_positions.extend(positions)
                        full_text = full_text[len(remaining_text):]
                        break
        else:
            break
    
    return all_found_positions

def pdf_find_text(pdf_path, search_text, origin_text, dpi=300):
    try:
        if search_text == "" or origin_text == "":
            return []
        if not os.path.exists(pdf_path):
            return []
        pdf_doc = fitz.open(pdf_path)
        
        # 检查origin_text是否存在于PDF中
        origin_text_positions = find_text_in_pdf(pdf_doc, origin_text)
        if len(origin_text_positions) == 0:
            pdf_doc.close()
            return []
        
        # 获取origin_text在PDF中的所有位置
        found_positions = []
        for origin_position in origin_text_positions:
            page = pdf_doc.load_page(origin_position["page"] - 1)
            text_instances = page.get_text("dict")['blocks']
            for block in text_instances:
                if block['type'] == 0:
                    for line in block['lines']:
                        for span in line['spans']:
                            if origin_text in span['text']:
                                origin_start_idx = span['text'].find(origin_text)
                                origin_end_idx = origin_start_idx + len(origin_text)
                                
                                # 查找search_text在origin_text中的位置
                                search_start_idx = origin_text.find(search_text)
                                if search_start_idx == -1:
                                    continue
                                search_end_idx = search_start_idx + len(search_text)
                                
                                # 计算search_text的坐标
                                char_width = (span["bbox"][2] - span["bbox"][0]) / len(span["text"])
                                search_x0 = span["bbox"][0] + (origin_start_idx + search_start_idx) * char_width
                                search_x1 = search_x0 + len(search_text) * char_width
                                
                                found_positions.append({
                                    "page": origin_position["page"],
                                    "text": search_text,
                                    "start_pixel": (search_x0 * (dpi / 72), span["bbox"][1] * (dpi / 72)),
                                    "end_pixel": (search_x1 * (dpi / 72), span["bbox"][3] * (dpi / 72))                             
                                })
        
        pdf_doc.close()
        return found_positions
    except Exception as e:
        traceback.print_exc()
        return []


def locate_text(page_number,ocr_data,parse_data):
    # Check if text exists in raw_text
    text = None
    raw_text = None
    blob = None
    if "extract_content" in parse_data:
        text = parse_data["extract_content"]
    
    if len(ocr_data) > 0 and "ocr" in ocr_data[0]:
        if "raw_text" in ocr_data[0]["ocr"]:
            raw_text = ocr_data[0]["ocr"]["raw_text"]
        if "blob" in ocr_data[0]["ocr"]:
            blob = ocr_data[0]["ocr"]["blob"]
    
    if text == None or raw_text == None or blob == None:
        return parse_data

    if not any(text in line for line in raw_text):
        return parse_data
    line_index = -1
    if raw_text:
        for idx, line in enumerate(raw_text):
            if text in line:
                line_index = idx
                break
    if line_index != -1:
        # Process the corresponding blob group
        if line_index < len(blob):
            group = blob[line_index]
            # Find matching text in blob and collect corresponding boxes
            matching_boxes = []
            for item in group:
                if text.startswith(item["text"]):
                    matching_boxes.append(item["box"])
                    text = text[len(item["text"]):]  # Trim the matched part from text

                if not text:  # All parts of the text matched
                    break

            # If all parts of text matched, calculate the bounding box
            if matching_boxes:
                found_positions = []
                top_left = matching_boxes[0][0]  # Top-left of the first box
                bottom_right = matching_boxes[-1][2]  # Bottom-right of the last box
                found_positions.append({
                                    "page": page_number,
                                    "text": text,
                                    "start_pixel": top_left,
                                    "end_pixel": bottom_right   
                                })
                
                parse_data["position"] = parse_data
                return parse_data

    return parse_data


def fix_min_len_resize(img, min_l, max_len=2500):
    h, w = img.shape[0:2]
    ratio = float(min_l) / min(h, w)
    ratio = min(max_len / max(h, w), ratio)
    new_h, new_w = int(ratio * h), int(ratio * w)
    res_img = cv2.resize(img, (new_w, new_h))
    res_ratio = (float(w) / new_w, float(h) / new_h)
    return res_img, res_ratio

if __name__ == '__main__':
    pdf_path = "/home/senscape/workspace/dataExtraction/data/uploads/templates/out/智能审核6.pdf"
    origin_text = "采 购 人: 中国共产党山东省委员会政法委员会"
    search_text = "中国共产党山东省委员会政法委员会"
    result = pdf_find_text(pdf_path, search_text, origin_text)
    print(result)
