def expand_board_with_percent(board, target_width, target_height):
    # Calculate how many '%' characters to add for width and height
    additional_width = target_width - len(board[0])
    additional_height = target_height - len(board)

    # Half the additional characters for symmetrical padding
    left_padding = additional_width // 2
    right_padding = additional_width - left_padding

    top_padding = additional_height // 2
    bottom_padding = additional_height - top_padding

    # Add '%' characters to each row
    expanded_board = []
    for row in board:
        expanded_row = '%' * left_padding + row + '%' * right_padding
        expanded_board.append(expanded_row)

    # Add '%' rows to the top and bottom of the board
    percent_row = '%' * target_width
    for _ in range(top_padding):
        expanded_board.insert(0, percent_row)
    for _ in range(bottom_padding):
        expanded_board.append(percent_row)

    return expanded_board
# board = [
#     '%%%%%%%%%%%%%%',
#     '%..o.       4%',
#     '%o ..       2%',
#     '%            %',
#     '%            %',
#     '%1       .. o%',
#     '%3       .o..%',
#     '%%%%%%%%%%%%%%'
# ]
#
# expanded = expand_board_with_percent(board, 34, 18)
# for row in expanded:
#     print(row)






