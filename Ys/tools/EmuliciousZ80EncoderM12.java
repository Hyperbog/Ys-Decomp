/*
 * Independent opcode encoder adapter for user-supplied Emulicious.jar.
 * The opcode selection is performed by Emulicious's own assembler.Z80Assembler.
 * This adapter only serializes the public Z80Instruction descriptor into bytes,
 * with standard Z80 relative-address and indexed-displacement positioning.
 * Neither Emulicious binaries nor commercial ROM content belongs in Git.
 */
import assembler.Z80Assembler;
import assembler.Z80Instruction;
import assembler.parsers.ExpressionEvaluator;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;

public final class EmuliciousZ80EncoderM12 {
    private static int parseNumber(CharSequence expr) {
        String value = expr.toString().trim().replace("$", "0x");
        if (value.startsWith("-0x")) return -(int)Long.parseLong(value.substring(3), 16);
        if (value.startsWith("+0x")) return (int)Long.parseLong(value.substring(3), 16);
        return Integer.decode(value);
    }

    static byte[] encode(Z80Instruction insn, int pc) {
        java.io.ByteArrayOutputStream out = new java.io.ByteArrayOutputStream();
        int prefix = insn.getPrefix();
        int op = insn.getOpCode();
        if (prefix != 0) out.write(prefix);
        if (op > 0xff) out.write((op >>> 8) & 255);
        if (prefix != 0 && (op >>> 8) == 0xcb) {
            out.write(insn.getDisplacement() & 255);
        }
        out.write(op & 255);
        if (prefix != 0 && insn.hasDisplacement() && (op >>> 8) != 0xcb) {
            out.write(insn.getDisplacement() & 255);
        }
        int arg = insn.getArg();
        if (insn.getArgSize() == 1) {
            if (insn.isRelative()) {
                int disp = (arg - pc - insn.getSize()) & 0xffff;
                if (disp > 127 && disp < 0xff80)
                    throw new IllegalArgumentException("relative branch out of range");
                arg = disp;
            }
            out.write(arg & 255);
        } else if (insn.getArgSize() == 2) {
            out.write(arg & 255);
            out.write((arg >>> 8) & 255);
        } else if (insn.getArgSize() != 0) {
            throw new IllegalArgumentException("unknown operand length");
        }
        byte[] result = out.toByteArray();
        if (result.length != insn.getSize())
            throw new IllegalArgumentException("descriptor length " + insn.getSize()
                + " differs from emitted length " + result.length);
        return result;
    }

    public static void main(String[] args) throws Exception {
        ExpressionEvaluator eval = EmuliciousZ80EncoderM12::parseNumber;
        Z80Assembler assembler = new Z80Assembler(eval);
        BufferedReader reader = new BufferedReader(new InputStreamReader(System.in, StandardCharsets.UTF_8));
        for (String line; (line = reader.readLine()) != null;) {
            int sep = line.indexOf('\t');
            if (sep < 1) { System.out.println("ERROR\tbad request"); continue; }
            String address = line.substring(0, sep);
            String mnemonic = line.substring(sep + 1);
            try {
                int pc = Integer.parseInt(address, 16);
                Z80Instruction instruction = assembler.assemble(mnemonic);
                if (instruction == null || !instruction.isValid())
                    throw new IllegalArgumentException("unrecognized opcode");
                byte[] bytes = encode(instruction, pc);
                StringBuilder hex = new StringBuilder();
                for (byte b : bytes) hex.append(String.format("%02X", b & 255));
                System.out.println(address + "\t" + hex);
            } catch (Exception e) {
                System.out.println(address + "\tERROR:" + e.getClass().getSimpleName() + ":"
                    + e.getMessage().replace('\n', ' '));
            }
        }
    }
}
