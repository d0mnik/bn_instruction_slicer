from binaryninja import BinaryView, PluginCommand, Variable, log
from binaryninja.enums import HighlightStandardColor
from queue import Queue


def slicer(bv: BinaryView, address: int, direction: str):
    seen: list[Variable] = []
    colorize: list[int] = []
    colorize.append(address)

    func = bv.get_functions_containing(address)[0]

    mlil_func = func.mlil
    llil = func.get_low_level_il_at(address)
    if llil is None or llil.mlil is None:
        log.log_error(f"Unable to get MLIL instruction at address {address:x}.")
        return
    instr = llil.mlil
    ### forward slice
    if direction == "F":
        q = Queue()
        for i in instr.vars_written:
            q.put(i)
        while not q.empty():
            var = q.get()
            seen.append(var)
            uses = mlil_func.get_var_uses(var)
            for i in uses:
                colorize.append(i.address)
                for j in i.vars_written:
                    if j in seen:
                        continue
                    q.put(j)

    # backward slice
    elif direction == "B":
        q: Queue[Variable] = Queue()
        for i in instr.vars_read:
            q.put(i)
        while not q.empty():
            var = q.get()
            seen.append(var)
            definitions = mlil_func.get_var_definitions(var)
            if len(definitions) == 0:
                continue
            for definition in definitions:
                colorize.append(definition.address)
                for j in definition.vars_read:
                    if j in seen:
                        continue
                    q.put(j)

    bv.begin_undo_actions()
    for i in colorize:
        func.set_user_instr_highlight(i, HighlightStandardColor.BlueHighlightColor)
    bv.commit_undo_actions()


def slice_backwards(bv: BinaryView, address: int):
    slicer(bv, address, "B")


def slice_forward(bv: BinaryView, address: int):
    slicer(bv, address, "F")


PluginCommand.register_for_address(
    "Instruction Slicer\\Backward slicing",
    "Perform backward slicing from this address",
    slice_backwards,
)
PluginCommand.register_for_address(
    "Instruction Slicer\\Forward slicing",
    "Perform forward slicing from this address",
    slice_forward,
)
