
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
import logging


def plot(x, y11, y21 = None, title = None, yLabel = None, text = None, label = None, fName = "", show = False):
    # --- Global styling ---
    plt.style.use("seaborn-v0_8-whitegrid")   # Modern seaborn-like style
    #plt.style.use("seaborn-v0_8-paper")   # Modern seaborn-like style
    # or
    #plt.style.use("ggplot")                   # R-style ggplot theme

    plt.rcParams.update({
        "font.size": 12,                # Base font size (now applies to the textbox at the top)
        "axes.labelsize": 14,           # x- and y axis labels font size
        "axes.titlesize": 14,           # Title font size
        "xtick.labelsize": 12,          # x-axis tick label font size (as in example 02/24 - 04/24)
        "ytick.labelsize": 12,          # y-axis tick label font size (numbers on the y-axis)
        "legend.fontsize": 12,          # Legend text font size (as in "Min båt")
        "lines.linewidth": 2.5,         # Thickness of plitted lines
        "lines.markersize": 8           # Marker size (circles, triangles) if used
    })

    sDate = []
    spanDays = x[0].daysTo(x[1])
    spanMonth = int(spanDays/30)

    spanMonth -= 1
    for date in x:
         sDate.append(date.addMonths(-int(spanMonth)))
    
    # --- Data ---
    y1 = y11[1: len(y11)]
    if y21 != None:
        y2 = y21[1: len(y21)]
    
    width = 0.25
    dx = np.arange(len(x))
    #dsDate = np.arange(len(sDate))
    xT = [n.toPython() for n in x]
    sDateT = [n.toPython() for n in sDate]
    xl = np.array(xT)
    sDatel = np.array(sDateT)
    xf = [n.strftime("%m/%y") for n in xl]
    sDatef = [n.strftime("%m/%y") for n in sDatel]          # format date label

    xNew = []
    i = 0
    for date in xf:
         xNew.append(sDatef[i] + " - " + xf[i])
         i += 1


    # --- Figure ---
    fig, ax = plt.subplots(figsize=(8,5), constrained_layout=False)
 
    # Adjust the margins around the plot area
    plt.subplots_adjust(
        left=0.11,                  # leave 11% for left margin, used by yaxis labe
        right=0.97,                 # leave 3% for rigth margin
        top=0.83,                   # leave 17% at top for title area
        bottom=0.08                 # leave 8% for bottom margin
    )

    if y21 is not None:
        # Two bars → offset left and right
        mBars = ax.bar(dx - width/2, y1, width = width, label = "Min båt", color='red')
        aBars = ax.bar(dx + width/2, y2, width = width, label = label, color = 'blue')
    else:
        # Single bar → centered on tick
        mBars = ax.bar(dx, y1, width=width, label="Min båt", color='red')     


    for bar in mBars:
        height = bar.get_height()
        
        if abs(height) >= 100:
                label = f"{height:.0f}"
        elif abs(height) >= 1:
                label = f"{height:.1f}"
        else:
                label = f"{height:.2f}"

        ax.text(
            bar.get_x() + bar.get_width()/2,    # x-position (center of bar)
            height,                             # y-position (top of bar)
            label,                    # text (formatted)
            ha='center', va='bottom',           # text alignment
            fontsize=10                         # override base font size
        )

    if y21 is not None:
        for bar in aBars:
            height = bar.get_height()

            if abs(height) >= 100:
                label = f"{height:.0f}"
            elif abs(height) >= 1:
                label = f"{height:.1f}"
            else:
                label = f"{height:.2f}"

            ax.text(
                bar.get_x() + bar.get_width()/2,    # x-position (center of bar)
                height,                             # y-position (top of bar)
                label,                    # text (formatted)
                ha='center', va='bottom',           # text alignment
                fontsize=10                         # override base font size
            )


    # Labels & title
    #ax.plot(x, y, linewidth=2.5, color="tab:blue", label="Signal")
    ylabel = yLabel
    ax.set_ylabel(ylabel)
    ax.set_xticks(dx)
    ax.set_xticklabels(xNew)
    ax.set_title(title)
    ax.legend()

     # --- TextBox ---
     # Place a centralized textbox 5% above the axis area
    ax.text(
        0.5, 1.05, text,
        transform=ax.transAxes,
        ha="center",
        bbox=dict(boxstyle="round", fc="none", ec = "none", alpha=0.2)       # invisible frame, remove ec for frame
    )

    # --- Grid ---
    # Use horizontal grid with dotted style
    ax.grid(True, axis='y',linestyle=':', alpha=0.8)    # 
    ax.grid(False, axis='x')
    
    # Clean up spines
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    #ax.spines["left"].set_visible(False)
    #ax.spines["bottom"].set_visible(False)

    # Legend
    ax.legend(frameon=True)

    # Save high-resolution
    #fig.savefig("nice_figure.pdf")

    if (show):         
        plt.show()
    if (fName != ""):
        plt.savefig(fName) 
    plt.close()

    return fig



def save_figs_to_pdf(figs, pdf_path, metadata=None, close=True, tight=True):
    """
    Save a list of matplotlib Figure objects to a single multi-page PDF.

    Args:
        figs (list[matplotlib.figure.Figure]): figures to save, in order.
        pdf_path (str | Path): output path like 'OUTDIR/rapport.pdf'.
        metadata (dict | None): optional metadata for the PDF (Title, Author, etc.).
        close (bool): whether to close figures after saving (recommended).
        tight (bool): apply bbox_inches='tight' to avoid clipping.
    """
    #pdf_path = Path(pdf_path)
    #pdf_path.parent.mkdir(parents=True, exist_ok=True)
    
    bbox = "tight" if tight else None
    i = 0
    with PdfPages(pdf_path) as pdf:
        if metadata:
            info = pdf.infodict()
            # Only set known keys if provided
            for k, v in metadata.items():
                info[k] = v
        for fig in figs:   
            if (i == 0):
                fig.text(0.1, 1.5, "FHF FiskInfoplattformen", fontsize=14)
                fig.text(0.1, 1.45, "Figurer fra bærekraftsmodulen", fontsize=12)

            pdf.savefig(fig, bbox_inches=bbox, pad_inches=0.2)
            i += 1
            if close:
                plt.close(fig)

    logging.info(f"PDF file saved: {pdf_path}")


        
    