# Karyotype Plotting: How It Works

## Overview
The `plot_karyoplot()` function in `/_org/saliogen/bluegenomics/plotting.py` generates karyotype plots showing chromosome ideograms with integration site annotations.

## Step-by-Step Process

### 1. Parse Ideogram TSV File (Lines 57-65)

```python
with open(supported_genomes[genome_id]) as karyo_f:
    lines = [x.replace(os.linesep, "").split() for x in karyo_f.readlines()]

    for chromosome in chromosomes:
        karyo_dict[chromosome] = [
            [y[0], int(y[1]), int(y[2]), y[3], y[4]]
            for y in [x for x in lines if x[0] == chromosome]
        ]
```

**What it does:**
- Reads `Human_hg38_ideogram.tsv` which contains 1479 lines of chromosome band data
- Each line has 5 tab-separated columns: `chrom chromStart chromEnd name gieStain`
- Example: `chr1	0	2300000	p36.33	gneg`
- The header line `#chrom chromStart chromEnd name gieStain` is naturally filtered out because `'#chrom'` never matches actual chromosome names like `'chr1'`
- Builds `karyo_dict` mapping each chromosome to its list of bands

**Result:** `karyo_dict['chr1']` contains 63 bands for chromosome 1, each with position and staining pattern.

### 2. Calculate Chromosome Lengths (Lines 70-76)

```python
def get_chromosome_length(chromosome):
    chromosome_start = float(min([x[1] for x in karyo_dict[chromosome]]))
    chromosome_end = float(max(x[2] for x in karyo_dict[chromosome]))
    return chromosome_end - chromosome_start

chromosome_lengths = {
    chromosome: get_chromosome_length(chromosome) for chromosome in chromosomes
}
```

**What it does:**
- For each chromosome, finds the minimum start position and maximum end position
- chr1: 0 to 248,956,422 bp = 248.9 Mb
- chrY: 0 to 57,227,415 bp = 57.2 Mb (smallest)

### 3. Set Up Plot Canvas (Lines 67-69, 78-79)

```python
fig, ax = plt.subplots()
fig.set_size_inches(18.5, 10.5)
ax.set_xlim([0.0, DIM * (1.1)])  # xlim: 0 to 1.1
ax.set_ylim([0.0, DIM])           # ylim: 0 to 1.0
```

**What it does:**
- Creates a matplotlib figure 18.5" x 10.5"
- X-axis spans 0 to 1.1 (normalized coordinates)
- Y-axis spans 0 to 1.0

### 4. Calculate Chromosome Positions (Lines 81-88)

For 24 chromosomes (chr1-22, chrX, chrY):

```python
def plot_chromosome(chromosome, order):
    x_start = order * DIM * (1 / len(chromosome_lengths))
    x_end = x_start + (DIM * (1 / (len(chromosome_lengths) * 2)))
    y_start = DIM * 0.9 * (chromosome_length / chromosome_length_1)
    y_end = DIM * 0.1
```

**Example calculations** (with `order = idx + 1`):
- **chr1** (order=1): x_start=0.0417, x_end=0.0625, y_start=0.9, y_end=0.1
- **chr2** (order=2): x_start=0.0833, x_end=0.1042, y_start=0.73, y_end=0.1
- **chrY** (order=24): x_start=1.0, x_end=1.021, y_start=0.21, y_end=0.1

**Why idx+1:** Creates a small left margin (0 to 0.0417) for visual spacing

### 5. Draw Chromosome Bands (Lines 95-110)

```python
for index, piece in enumerate(karyo_dict[chromosome]):
    current_height = piece[2] - piece[1]
    current_height_sc = ((y_end - y_start) / chromosome_length) * current_height
    color = colors[piece[4]]  # gpos100, gpos75, gneg, acen, etc.

    r = Rectangle(
        (x_start, y_previous),
        x_end - x_start,
        current_height_sc,
        color=color,
    )
    ax.add_patch(r)
```

**What it does:**
- For each band in the chromosome (e.g., 63 bands for chr1)
- Calculates the scaled height based on band size in base pairs
- Selects color based on Giemsa stain pattern:
  - `gneg`: white (255, 255, 255)
  - `gpos100`: black (0, 0, 0)
  - `gpos75`: dark gray (130, 130, 130)
  - `gpos50`: medium gray (200, 200, 200)
  - `acen`: red (217, 47, 39) - centromere
- Draws a Rectangle patch for each band

**Result:** Each chromosome displays with its characteristic banding pattern

### 6. Draw Chromosome Caps (Lines 113-148)

```python
w1 = Wedge((center_x, y_start), radius, 0, 180, ...)  # Top cap
w2 = Wedge((center_x, y_end), radius, 180, 0, ...)    # Bottom cap
```

**What it does:**
- Adds semicircular caps at the top (p-arm telomere) and bottom (q-arm telomere) of each chromosome
- Draws vertical lines on the sides
- Creates the characteristic rounded chromosome appearance

### 7. Plot Integration Sites (Lines 151-173)

```python
for md in annotations.get(chromosome, []):
    pos = md["pos"]
    offset = md.get("offset", np.random.normal(loc=0.009, scale=0.004))
    color = md.get("color", "blue")

    ax.plot(
        [x_end + (DIM * 0.003 + offset)],
        [y_start + (y_end - y_start) * (pos / chromosome_length)],
        ".",
        color=color,
    )
```

**What it does:**
- For each integration site in the annotations dict
- Calculates y-position based on genomic position relative to chromosome length
- Adds random jitter (offset) to avoid overlapping points
- Plots a dot to the right of the chromosome at the corresponding position
- Default color: blue

**Example:** Integration at chr1:100,000,000
- Relative position: 100M / 248.9M = 0.402
- Y-coordinate: 0.9 + (0.1 - 0.9) * 0.402 = 0.578
- X-coordinate: 0.0625 + 0.003 + jitter ≈ 0.075

### 8. Add Chromosome Labels (Line 175)

```python
ax.text(center_x, y_end - (DIM * 0.07), chromosome)
```

**What it does:**
- Places chromosome name (e.g., "chr1") below each chromosome
- Positioned at center_x, slightly below the bottom cap

### 9. Render All Chromosomes (Lines 177-180)

```python
for idx, chromosome in enumerate(chromosomes):
    plot_chromosome(chromosome, idx + 1)

plt.axis("off")
plt.show()
```

**What it does:**
- Loops through all 24 chromosomes
- Calls `plot_chromosome()` with order parameter (1 to 24)
- Turns off axis labels and ticks
- Displays the complete karyotype plot

## Why It Should Work

1. **TSV parsing is correct**: Header is naturally filtered because `'#chrom' != 'chr1'`
2. **All imports are present**: `Rectangle`, `Wedge`, `numpy`, `matplotlib`
3. **Math is correct**: Chromosome positions span 0.0417 to ~1.02 (within xlim of 0-1.1)
4. **Colors are defined**: All Giemsa stain patterns have color mappings
5. **Data structure matches**: `annotations` dict format is correct

## Expected Output

The plot should display:
- 24 chromosomes arranged horizontally across the figure
- Each chromosome showing its characteristic G-banding pattern
- Integration sites as blue dots positioned along the chromosome length
- Chromosome labels below each ideogram
- Chromosomes scaled by relative length (chr1 tallest, chrY shortest)

