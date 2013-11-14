#include "main.h"
#include <iostream>
#include <string>
#include <boost/lexical_cast.hpp>

// inline includes
#include "cpu.cpp"
#include "memory.cpp"

CPU cpu;
Memory mem;

uint8_t asm_of, asm_zf, asm_sf, asm_cf;
uint32_t asm_eax;
int current_line;

inline void test_zf()
{
    if (int(cpu.get_zf()) == asm_zf)
        return;
    std::cout << "Invalid ZF at " << current_line << std::endl;
    exit(0);
}

inline void test_sf()
{
    if (int(cpu.get_sf()) == asm_sf)
        return;
    std::cout << "Invalid SF " << current_line << std::endl;
    exit(0);
}

inline void test_of()
{
    if (int(cpu.get_of()) == asm_of)
        return;
    std::cout << "Invalid OF " << current_line << std::endl;
    exit(0);
}

inline void test_cf()
{
    if (int(cpu.get_cf()) == asm_cf)
        return;
    std::cout << "Invalid CF " << current_line << std::endl;
    exit(0);
}

inline void test_eax()
{
    if (cpu.reg[EAX] == asm_eax)
        return;
    std::cout << "Invalid EAX " << current_line << std::endl;
    exit(0);
}

inline void test_ax()
{
    if (*cpu.reg16[AX] == (asm_eax & 0xFFFF))
        return;
    std::cout << "Invalid AX " << current_line << std::endl;
    exit(0);
}

inline void test_al()
{
    if (*cpu.reg8[AL] == (asm_eax & 0xFF))
        return;
    std::cout << "Invalid AL " << current_line << std::endl;
    exit(0);
}

inline void test_flags()
{
    test_of();
    test_sf();
    test_zf();
    test_cf();
}

#define PUSH_REGS() asm("push %eax\n\t")
#define POP_REGS() asm("movl %eax, _asm_eax\n\t"\
                       "seto _asm_of\n\t"\
                       "setc _asm_cf\n\t"\
                       "setz _asm_zf\n\t"\
                       "sets _asm_sf\n\t"\
                       "pop %eax\n\t")

inline void test_add_dword(uint32_t a, uint32_t b)
{
    cpu.reg[EAX] = cpu.add_dword(a, b);
    PUSH_REGS();
    asm("movl %0, %%eax" : : "g" (a));
    asm("addl %0, %%eax" : : "g" (b));
    POP_REGS();
    test_flags();
    test_eax();
}

inline void test_add_byte(uint8_t a, uint8_t b)
{
    *cpu.reg8[AL] = cpu.add_byte(a, b);
    PUSH_REGS();
    asm("movb %0, %%al" : : "g" (a));
    asm("addb %0, %%al" : : "g" (b));
    POP_REGS();
    test_flags();
    test_al();
}

#define LOG(v) current_line = __LINE__; v;

int main(int argc, const char ** argv)
{
    std::cout << "Running tests" << std::endl;

    // add
    // dword
    LOG(test_add_dword(-2, 2));
    LOG(test_add_dword(500, 2));
    LOG(test_add_dword(0xFFFFFFFF, 1));

    // byte
    LOG(test_add_byte(-2, 2));
    LOG(test_add_byte(255, 2));
    LOG(test_add_byte(-73, 1));

    std::cout << "Done" << std::endl;
    return 0;
}