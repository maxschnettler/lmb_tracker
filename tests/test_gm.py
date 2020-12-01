import unittest
from copy import deepcopy
from unittest.mock import MagicMock
import numpy as np

import lmb.gm

class TestGM(unittest.TestCase):
    def setUp(self):
        self.params = MagicMock()

        self.params.dim_x = 4
        self.params.log_p_detect = np.log(0.99)
        self.params.log_kappa = np.log(0.01)
        self.params.log_q_detect = np.log(1 - 0.99)
        # observation noise covariance
        self.params.R: np.ndarray = np.asarray([[0., 0.],
                                        [0., 0.]], dtype='f4')
        # process noise covariance
        self.params.Q: np.ndarray = np.asarray([[5., 0., 10., 0.],
                                [0., 5., 0., 10.],
                                [10., 0., 20., 0.],
                                [0., 10., 0., 20.]], dtype='f4')
        # Motion model: state transition matrix
        self.params.F: np.ndarray = np.asarray([[1., 0., 1., 0.],
                                [0., 1., 0., 1.],
                                [0., 0., 1., 0.],
                                [0., 0., 0., 1.]], dtype='f4')
        # Observation model
        self.params.H: np.ndarray = np.asarray([[1., 0., 0., 0.],
                                [0., 1., 0., 0.]], dtype='f4')
        # Initial state covariance matrix
        self.params.P_init: np.ndarray = np.asarray([[10., 0., 0., 0.],
                                    [0., 10., 0., 0.],
                                    [0., 0., 10., 0.],
                                    [0., 0., 0., 10.]], dtype='f4')
        self.pdf = lmb.GM(self.params)
        self.pdf.mc = np.append(self.pdf.mc[0], self.pdf.mc[0])
        self.pdf.mc[0]['x'] = np.asarray([1., 0., 0.5, 0.5])
        self.pdf.mc[1]['x'] = np.asarray([-5., 0., -1., 2])
        self.pdf.mc[0]['log_w'] = np.log(1 / len(self.pdf.mc))
        self.pdf.mc[1]['log_w'] = np.log(1 / len(self.pdf.mc))

    def test_predict(self):
        mc_prior = deepcopy(self.pdf.mc)
        self.pdf.predict()
        # Test states
        self.assertTrue(np.allclose(self.pdf.mc[0]['x'], np.asarray([1.5, 0.5, 0.5, 0.5])))
        self.assertTrue(np.allclose(self.pdf.mc[1]['x'], np.asarray([-6., 2., -1., 2.])))
        # Test log_w
        self.assertTrue(np.allclose(self.pdf.mc['log_w'], mc_prior['log_w']))
        # Test shape of P
        self.assertEqual(self.pdf.mc['P'].shape, mc_prior['P'].shape)

    def test_correct(self):
        mc_prior = deepcopy(self.pdf.mc)
        z = np.asarray([0, -1])
        self.pdf.correct(z)
        
        # Test resulting shapes of arrays
        self.assertEqual(self.pdf.mc['x'].shape, mc_prior['x'].shape)
        self.assertEqual(self.pdf.mc['P'].shape, mc_prior['P'].shape)
        # Test values of P: Every value of the covariance matrices have to be 
        # smaller or equal the prior value before correction
        self.assertTrue((self.pdf.mc['P'] <= mc_prior['P']).all())
        # Test whether mixture component weights sum up to 1
        self.assertAlmostEqual(np.sum(np.exp(self.pdf.mc['log_w'])), 1.)

        # Missed detection
        prior = deepcopy(self.pdf)
        self.pdf.correct(None)
        self.assertTrue(np.allclose(self.pdf.mc['x'], prior.mc['x']))
        self.assertTrue(np.allclose(self.pdf.mc['P'], prior.mc['P']))
        self.assertTrue(np.allclose(self.pdf.mc['log_w'], prior.mc['log_w']))
        self.assertAlmostEqual(self.pdf.log_eta_z, prior.log_w_sum + self.params.log_q_detect)

    def test_overwrite_with_merged_pdf(self):
        mc_prior = deepcopy(self.pdf)
        pdfs = [self.pdf, mc_prior]
        log_weights = [np.log(0.75), np.log(0.25)]
        len_mc_pdfs = np.sum([len(pdf.mc) for pdf in pdfs])
        self.pdf.overwrite_with_merged_pdf(pdfs, log_weights)

        # Test number of resulting mixture components
        self.assertEqual(len(self.pdf.mc), len_mc_pdfs)
        # Test whether mixture component weights sum up to 1
        self.assertAlmostEqual(np.sum(np.exp(self.pdf.mc['log_w'])), 1.)
