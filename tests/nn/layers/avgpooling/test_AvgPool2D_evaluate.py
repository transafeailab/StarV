import unittest
import numpy as np
import sys, os
import mat73

sys.path.insert(0, "tests/nn/layers/avgpooling")
from test_inputs.sources import *

sys.path.insert(0, "engine/nn/layers/avgpooling")
from averagepooling2dlayer import *
    
def read_csv_data(path):        
    return np.array(list(mat73.loadmat(path).values())[0])

class TestAveragePooling2DLayer_evalate(unittest.TestCase):
    """
        Tests AveragePooling2D layer's evaluate method
    """

    def test_basic(self):
        
        test_pool_size = np.reshape(read_csv_data(sources[AVGP2D_TEST_EVALUATE_INIT][AVGP2D_TEST_POOL_SIZE_ID]), (1,2))
        test_padding_size = np.reshape(read_csv_data(sources[AVGP2D_TEST_EVALUATE_INIT][AVGP2D_TEST_PADDING_SIZE_ID]), (1, 2))
        test_stride = np.reshape(read_csv_data(sources[AVGP2D_TEST_EVALUATE_INIT][AVGP2D_TEST_STRIDE_ID]), (1, 2))
        test_num_inputs = read_csv_data(sources[AVGP2D_TEST_EVALUATE_INIT][AVGP2D_TEST_NUM_INPUTS_ID])
        test_input_names = read_csv_data(sources[AVGP2D_TEST_EVALUATE_INIT][AVGP2D_TEST_INPUT_NAMES_ID])
        test_num_outputs = read_csv_data(sources[AVGP2D_TEST_EVALUATE_INIT][AVGP2D_TEST_NUM_OUTPUTS_ID])
        test_output_names = read_csv_data(sources[AVGP2D_TEST_EVALUATE_INIT][AVGP2D_TEST_OUTPUT_NAMES_ID])

        avgpool2d_layer = AveragePooling2DLayer('average_pooling_2d_layer',\
                                   test_pool_size, test_stride, test_padding_size, test_num_inputs, \
                                   test_input_names, test_num_outputs, test_output_names)

        
        input = np.random.rand(1, 28, 28)
        
        avgpool2d_layer.evaluate(input)
        
        
if __name__ == '__main__':
    unittest.main()