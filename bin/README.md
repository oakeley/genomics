Setup
-----
conda create -n saliogen python=3.11
conda activate saliogen
conda install pip
# Install picard
sudo dpkg -i /_org/saliogen/bin/jdk-25_linux-x64_bin.deb
mv /home/edward/anaconda3/bin/java /home/edward/anaconda3/bin/java.bak
ln -s /usr/lib/jvm/jdk-25-oracle-x64/bin/java /home/edward/anaconda3/bin/java
# Install bwa
sudo apt install bwa
# Install samtools
sudo apt install samtools
# Install fastqc
sudo apt install fastqc
# Install multiqc
conda install multiqc
# Install umi_tools
conda install bioconda::umi_tools
# Install pip dependencies
pip install numpy pandas pysam biopython pyranges plotly matplotlib seaborn jupyter ipython ipywidgets scipy scikit-learn tables tqdm
