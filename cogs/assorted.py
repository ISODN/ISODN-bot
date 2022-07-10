def split_msg_bylines(msg):
    lines = msg.split('\n')
    #print(lines)
    blocks = []
    current_msg = ''
    in_code_block = False
    for l in lines:
        if len(current_msg) + len(l) < 1900:
            current_msg += '\n'
            current_msg += l
        else:
            #print(current_msg)
            for i in current_msg:
                if i == '`':
                    in_code_block = not in_code_block
            if in_code_block:
                current_msg += '```'
            blocks.append(current_msg)
            in_code_block = False
            current_msg = '```' + l
    blocks.append(current_msg)
    #print(blocks)
    return blocks
