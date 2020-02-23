#!/usr/bin/env python3
import os
import sys
import subprocess
import argparse


failed_cases = []
n_passed = 0
n_cases = 0

script_dir = os.path.dirname(os.path.abspath(__file__))
compile_cmd = os.path.join(script_dir, '../compile')
arm_gcc = os.path.join(script_dir, './tools/arm-gcc')
arm_run = os.path.join(script_dir, './tools/arm-run')

def compile(f):
    try:
        subprocess.run([compile_cmd, f], timeout=5)
        subprocess.run([arm_gcc, os.path.basename(f).replace('.wacc', '.s')])
        out = subprocess.run([arm_run, 'a.out'], stdout=subprocess.PIPE, timeout=5)
        output = '' if not out.stdout else out.stdout.decode('utf-8')
        return (output, out.returncode)
    except subprocess.TimeoutExpired:
        return ("timeout", -1)
    except UnicodeDecodeError:
        return ("failed", -1)

def run_test(filename):
    global n_cases, n_passed, failed_cases
    n_cases += 1
    expected = {}
    infile = open(filename, 'rt')
    for line in infile:
        if line.startswith("#"):
            tks = line.split(" ")
            if tks[1].strip() in ['Output:', 'Exit:']:
                title = tks[1].strip()
                expected[title] = []
                for l in infile:
                    if not l.startswith("#"):
                        break
                    else:
                        ll = ' '.join(l.split(' ')[1:])
                        expected[title].append(ll)
    infile.close()
    output, retcode = compile(filename)
    if "Output:" in expected:
        expected_output = ''.join(expected['Output:'])
        if "#empty#" in expected_output:
            if len(output) != 0:
                failed_cases.append((filename, expected_output, output))
                return
        else:
            if expected_output.strip() == output.strip():
                expected_output_splitted = expected_output.split()
                output_splitted = output.split()
                for i in range(min(len(expected_output_splitted), len(output_splitted))):
                    if expected_output_splitted[i] != output_splitted[i] and expected_output_splitted[i] != "#addrs#" and expected_output_splitted[i] != "#runtime_error#":
                        failed_cases.append((filename, expected_output, output))
                        return

    if "Exit:" in expected:
        expected_ret = int(''.join(expected['Exit:']).strip())
        if  expected_ret == retcode:
            n_passed += 1
        else:
            failed_cases.append((filename, "Return code: {}".format(expected_ret), "Return code: {}".format(retcode)))
    else:
        if retcode == 0:
            n_passed += 1
        else:
            failed_cases.append((filename, "Return code: 0", "Return code: {}".format(retcode)))




with open(os.path.join(script_dir, "testsuite/excluded"), 'r') as excluded:
    excluded = excluded.read().split("\n")
excluded = [os.path.abspath(os.path.join("./testsuite", e)) for e in excluded if len(e) > 0]


def run_tests(path=os.path.join(script_dir, "./testsuite/valid")):
    for (root, dirs, files) in os.walk(path):
        for name in files:
            p = os.path.abspath(os.path.join(root, name))
            if p.endswith(".wacc") and p not in excluded:
                print(p)
                run_test(p)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dir", default=os.path.join(script_dir, "./testsuite/valid"))
    args = parser.parse_args()
    run_tests(args.dir)
    out = subprocess.run("rm *.s", stdout=subprocess.PIPE, timeout=5, shell=True)
    print("Passed {} / {} testcases".format(n_passed, n_cases))
    for index, (filename, expected, actual) in enumerate(failed_cases):
        print("{}. In {}".format(index + 1, filename))
        print("Expected:\n{}".format(expected.strip()))
        print("Actual:\n{}".format(actual.strip()))
