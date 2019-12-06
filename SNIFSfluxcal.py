import numpy as np
import argparse, glob, os, sys
from astropy.io import fits
from lmfit import Parameters, minimize

import matplotlib.pyplot as plt


from pyExtinction.pyExtinction import AtmosphericExtinction as AtmExt

def main(indir=None, channel=None, plot=True, verb=False):

	channel='BR' if channel is None else channel
	indir = './' if indir is None else indir

	for chan in list(channel):
		if verb: print('Working on channel: ' + chan)
		spex = find1DSpectra(indir=indir, channel=chan)
		
		if len(spex) == 0:
			print('WARNING: No 1D spectra found in dir "%s" for channel "%s" ' % (indir, chan))
			continue
		elif verb: print('\tFound %d 1D spectra in %s' % (len(spex), indir) )

		std_spex = findStdSpex(spex)
		if len(std_spex) == 0:
			print("WARNING: No standard star spectra found! No calibrations will be applied.")
			continue
		elif len(std_spex) < 3:
			print('WARNING: Only %d standard star spectra found, flux calibration will likely be poor quality!' % (len(std_spex)))
		elif verb:
			print('\t%d standard star spectra found.' % (len(std_spex)))

		if verb: print('\tFitting atm throughput and instr resp...')
		


class Spectrum:
	def __init__(self, fitsfile):
		self.fname = fitsfile
		if not os.path.exists(self.fname):
			raise IOError('Cannot find input spectrum: %s' % self.fname)
		else:
			self.flux, self.hdr = fits.getdata(self.fname, header=True)

		self.wl = self.hdr['CRVAL1'] + self.hdr['CDELT1']*np.arange(self.flux.size)
		self.varname = os.path.dirname(self.fname)+'/var_'+os.path.basename(self.fname)
		if not os.path.exists(self.varname):
			print('WARNING: Failed to find variance file %s' % self.varname)
			self.err = None
		else:
			self.err = np.sqrt(fits.getdata(self.varname))

		self.object = self.hdr['OBJECT']
		self.exptime = self.hdr['EXPTIME']
		self.channel=self.hdr['CHANNEL'][0]
		self.am = self.hdr['AIRMASS']
		self.jd = self.hdr['JD']
		self.mjd = self.jd - 2400000.5
		self.date = self.hdr['DATE-OBS']

	def __str__(self):
		outstr = """
### SNIFS spectrum ###
	->File: %s
	->Var: %s
	->Channel: %s
	->Object: %s
	->Exptime: %.1f
	->Airmass: %.2f
	->MJD-OBS: %.5f
	->DATE-OBS: %s
""" % (self.fname, self.varname, self.channel, self.object, self.exptime, 
						self.am, self.mjd, self.date)
		return outstr


def findStdSpex(spex):
	std_names, std_RA, std_DEC, std_Vmag, std_stype = np.genfromtxt('./standards.dat', comments='#', dtype=str, unpack=True)
	std_spex = []
	for ii, spec in enumerate(spex):
		if spec.object in list(std_names): std_spex.append(spec)
	return std_spex



def find1DSpectra(indir, channel):
	fnames = glob.glob(indir+'/spec_*_%s.fits' % channel)
	return [Spectrum(ff) for ff in fnames]



if __name__=='__main__':
	parser = argparse.ArgumentParser(description="Computes atmosperic and instrumental response from a set a SNIFS standard star spectra, then applies corrections to the science spectra.")

	parser.add_argument('--indir', '-d', help='Input directory containing the SNIFS 1D spectra.', default=None, type=str)
	parser.add_argument('--channel', '-c', help='Which channel to process. Default: BR', default='BR', choices=['B','R','BR','RB'])
	parser.add_argument('--plot', '-p', help='Show plots? Default: False', default=False, action='store_true')
	parser.add_argument('--verbose', '-v', help='Verbose output? Default: False', action='store_true')

	args = parser.parse_args()
	main(args.indir, args.channel, args.plot, args.verbose)
