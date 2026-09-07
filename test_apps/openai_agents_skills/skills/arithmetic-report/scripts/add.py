"""Add two integers and print a stable, inspectable result."""

import argparse


parser = argparse.ArgumentParser()
parser.add_argument("left", type=int)
parser.add_argument("right", type=int)
args = parser.parse_args()

print(f"{args.left} + {args.right} = {args.left + args.right}")

