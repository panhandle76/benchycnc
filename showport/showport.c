/*
 * showport.c: very simple example of port I/O
 *
 * Based on http://www.faqs.org/docs/Linux-mini/IO-Port-Programming.html
 *
 * Compile "sudo gcc -O2 -o showport showport.c"
 * run with "sudo ./showport (base1) (extended1) (mode) (base2) (extended2) (mode) ...
 * for example - "sudo ./showport 21D0 21C8 s 21C0 21B8 e"
 * mode s = SPP, e = EPP, n = no change
 * 
 * The register addresses can come from "lspci -v". For a MOSCHIP, usually the first
 * and third addresses on a dual port card are the bases, the extended registers are 
 * usually the second and fourth. The standard indicates that the extended register 
 * is 0x400 above the base, but this doesn't seem to be followed very often.
 */

#include <stdio.h>
#include <unistd.h>
//#include <asm/io.h>    /* My computer didn't have io.h in asm */
#include <sys/io.h>      /* but I found it here */
#include <stdlib.h>      /* added to stop an "exit not defined" warning, and for strtol */

void print_usage() {
  printf("  Usage: showport BASE_0 EXTENDED_0 s|S|e|E|n|N [ BASE_1 EXTENDED_1 s|S|e|E|n|N ] ...\n");
  printf("  s = SPP, e = EPP, n = No change\n");
}

int main(int argc, char *argv[])
{
  int base, extended;
  char index, ecr, mode;

  if (iopl(3)) {perror("iopl"); exit(1);}    /* Get access to the ports */

  index = argc - 1;         /* argument 1 is index 0 */
  if (index % 3 != 0) {     /* arguments need to be in groups of three */
      printf("  Not enough arguments - Base Extended Mode\n");
      print_usage();
      exit(0);
  }

  for (index = 1; index < argc; ++index) {  /* Convert each argument group into base, extended, and mode */
    base = strtol(argv[index], NULL, 16);
    ++index;
    extended = strtol(argv[index], NULL, 16);
    ++index;
    if ((argv[index][0] == 's') || (argv[index][0] == 'S')) { mode = 's'; }
    else if ((argv[index][0] == 'e') || (argv[index][0] == 'E')) { mode = 'e'; }
    else if ((argv[index][0] == 'n') || (argv[index][0] == 'N')) { mode = 'n'; }
    else { printf("  Invalid Mode - s|S|e|E|n|N\n"); print_usage(); exit(0); }

    printf("~~~~~\nBase @ 0x%x\n", base);
    printf("Extended @ 0x%x\n", extended);

    printf("DPR: %d\n", inb(base + 0));     /* Read and display all registers */
    printf("DSR: %d\n", inb(base + 1));
    printf("DCR: %d\n", inb(base + 2));
    printf("EPPA: %d\n", inb(base + 3));
    printf("EPPD: %d\n\n", inb(base + 4));

    printf("CFA: %d\n", inb(extended + 0));
    printf("CFB: %d\n", inb(extended + 1));
    printf("ECR: %d\n~~~~~\n", inb(extended + 2));

    ecr = inb(extended + 2);
    ecr &= 0x1F;  /* unset top three bits (mode) */

    if (mode == 'e') {
      outb((ecr |= 0x80), extended + 2);  /* set top three bits to 0b001 (EPP)*/
      printf("Setting mode to EPP\n");
    } else if (mode == 's') {
      outb((ecr |= 0x20), extended + 2);  /* set top three bits to 0b100 (SPP)*/
      printf("Setting mode to SPP\n");
    } else {
      printf("No mode change\n");
    }
    printf("ECR: %d\n~~~~~\n", inb(extended + 2));
  }

  if (iopl(0)) {perror("iopl"); exit(1);} /* We don't need the ports anymore */
  exit(0);

}

