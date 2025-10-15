#!/usr/bin/env python3
import json
import argparse
import sys
import os
import glob

TOL = 0.025


def load_positions(path):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Expect new structure with balls array and table_size
    if 'balls' not in data:
        raise ValueError(f"File {path} missing 'balls' array - expecting new JSON structure")
    
    balls = data['balls']
    table_size = data.get('table_size')
    
    # Handle new structure: balls have nested position object
    normalized_balls = []
    for b in balls:
        # Check if this is the new structure with nested position
        if 'position' in b and isinstance(b['position'], dict):
            pos = b['position']
            if 'x_norm' not in pos or 'y_norm' not in pos:
                raise ValueError(f"File {path} missing normalized coords in position for ball: {b}")
            # Flatten the structure
            normalized_ball = {
                'number': b.get('number'),
                'x': pos.get('x'),
                'y': pos.get('y'), 
                'x_norm': pos['x_norm'],
                'y_norm': pos['y_norm']
            }
        else:
            # Old structure: direct x_norm, y_norm
            if 'x_norm' not in b or 'y_norm' not in b:
                raise ValueError(f"File {path} missing normalized coords for ball: {b}")
            normalized_ball = b
        
        normalized_balls.append(normalized_ball)
    
    # Filter to only include balls 1-15
    filtered_balls = []
    for b in normalized_balls:
        num = b.get('number')
        if isinstance(num, int) and 1 <= num <= 15:
            filtered_balls.append(b)
        elif isinstance(num, str) and num.isdigit() and 1 <= int(num) <= 15:
            filtered_balls.append(b)
    
    return filtered_balls, table_size


def sort_balls(balls):
    # Sort by numeric 'number' ascending. Coerce number to int when possible.
    def get_num(b):
        num = b.get('number')
        if isinstance(num, int):
            return num
        if isinstance(num, str) and num.isdigit():
            return int(num)
        raise ValueError(f"Ball missing numeric 'number' field or not coercible to int: {b}")

    return sorted(balls, key=lambda b: get_num(b))


def compare(shot_balls, pattern_balls, tol=TOL):
    if len(shot_balls) != len(pattern_balls):
        return False, f"Different number of balls: shot={len(shot_balls)} pattern={len(pattern_balls)}"

    mismatches = []
    for i, (s, p) in enumerate(zip(shot_balls, pattern_balls), start=1):
        dx = abs(s['x_norm'] - p['x_norm'])
        dy = abs(s['y_norm'] - p['y_norm'])
        if dx <= tol and dy <= tol:
            continue
        else:
            mismatches.append({
                'index': i,
                'shot': s,
                'pattern': p,
                'dx': dx,
                'dy': dy
            })
    if not mismatches:
        return True, f"MATCH: all {len(shot_balls)} balls matched within tol={tol}"
    else:
        return False, mismatches


def apply_flip_to_norms(balls, mode):
    """Return a new list of balls with x_norm/y_norm flipped according to mode.
    mode: 'none', 'h', 'v', 'hv'"""
    flipped = []
    for b in balls:
        x = b['x_norm']
        y = b['y_norm']
        if mode == 'none':
            nx, ny = x, y
        elif mode == 'h':
            nx, ny = 1.0 - x, y
        elif mode == 'v':
            nx, ny = x, 1.0 - y
        elif mode == 'hv':
            nx, ny = 1.0 - x, 1.0 - y
        else:
            raise ValueError('Unknown flip mode: ' + str(mode))
        nb = dict(b)
        nb['x_norm'] = nx
        nb['y_norm'] = ny
        flipped.append(nb)
    return flipped


def main():
    parser = argparse.ArgumentParser(description='Compare shot and pattern position JSON files using normalized coordinates')
    parser.add_argument('shot', help='Shot JSON file')
    parser.add_argument('--patterns-dir', '-p', default='patterns/position', help='Directory containing pattern JSON files (default: patterns/positions)')
    parser.add_argument('--tol', type=float, default=TOL, help='Tolerance for x_norm and y_norm (default 0.025)')
    parser.add_argument('--order', action='store_true', help='Sort balls by number before comparison (default: compare in original JSON order)')

    args = parser.parse_args()

    try:
        shot, shot_table_size = load_positions(args.shot)
    except Exception as e:
        print('Failed to load shot file:', e)
        sys.exit(2)

    # Gather pattern files
    patterns_dir = args.patterns_dir
    pattern_files = sorted(glob.glob(os.path.join(patterns_dir, '*.json')))
    if not pattern_files:
        print(f"No pattern JSON files found in '{patterns_dir}'")
        sys.exit(2)

    modes = ['none', 'h', 'v', 'hv']
    matches = []
    best = {'count': None, 'pattern': None, 'mode': None, 'detail': None}

    for pat_fp in pattern_files:
        try:
            pattern, pattern_table_size = load_positions(pat_fp)
        except Exception as e:
            print(f"Skipping pattern '{pat_fp}': failed to load: {e}")
            continue

        # If counts differ, this pattern cannot match; record and continue
        if len(shot) != len(pattern):
            # treat as non-matching with a high mismatch count
            cnt = abs(len(shot) - len(pattern)) + 100000
            if best['count'] is None or cnt < best['count']:
                best.update({'count': cnt, 'pattern': pat_fp, 'mode': None, 'detail': f"Different counts: shot={len(shot)} pattern={len(pattern)}"})
            continue

        # Try flip modes
        for mode in modes:
            shot_flipped = apply_flip_to_norms(shot, mode)
            try:
                if args.order:
                    shot_s = sort_balls(shot_flipped)
                    pattern_s = sort_balls(pattern)
                else:
                    shot_s = shot_flipped
                    pattern_s = pattern
            except Exception as e:
                print(f"Error sorting for pattern '{pat_fp}' mode '{mode}': {e}")
                continue

            ok, detail = compare(shot_s, pattern_s, tol=args.tol)
            if ok:
                matches.append({'pattern': pat_fp, 'mode': mode})
                # we can stop checking other modes for this pattern
                break
            else:
                cnt = len(detail) if isinstance(detail, list) else 100000
                if best['count'] is None or cnt < best['count']:
                    best.update({'count': cnt, 'pattern': pat_fp, 'mode': mode, 'detail': detail})

    if matches:
        print('MATCH found:')
        for m in matches:
            print(f"  pattern: {m['pattern']}  flip: {m['mode']}")
        sys.exit(0)
    else:
        print('NO MATCH found in patterns directory.')
        if best['pattern']:
            print(f"Best candidate: {best['pattern']} (mode={best['mode']}) with {best['count']} mismatches")
            detail = best['detail']
            if isinstance(detail, str):
                print('Reason:', detail)
            else:
                print('Mismatches:')
                for m in detail:
                    i = m['index']
                    s = m['shot']
                    p = m['pattern']
                    print(f"#{i}: shot number={s.get('number')} pattern number={p.get('number')}")
                    print(f"  shot x_norm={s['x_norm']:.6f} y_norm={s['y_norm']:.6f}")
                    print(f"  pat  x_norm={p['x_norm']:.6f} y_norm={p['y_norm']:.6f}")
                    print(f"  dx={m['dx']:.6f} dy={m['dy']:.6f} (tol={args.tol})")
        sys.exit(1)


if __name__ == '__main__':
    main()
