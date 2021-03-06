# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Types."""

from __future__ import absolute_import
from __future__ import division

from __future__ import print_function


import numpy as np
import tensorflow as tf
from tensorflow_transform.beam import shared

from tensorflow_model_analysis.types_compat import Any, Callable, Dict, List, Optional, Text, Tuple, Union, NamedTuple

# pylint: disable=invalid-name

TensorType = Union[tf.Tensor, tf.SparseTensor]
TensorOrOperationType = Union[TensorType, tf.Operation]
DictOfTensorType = Dict[Text, TensorType]
TensorTypeMaybeDict = Union[TensorType, DictOfTensorType]

# Type of keys we support for prediction, label and features dictionaries.
KeyType = Union[Text, Tuple[Text, Ellipsis]]

# Value of a Tensor fetched using session.run.
TensorValue = Union[tf.SparseTensorValue, np.ndarray]

# Dictionary of Tensor values fetched.
# The dictionary maps original dictionary keys => ('node' => value).
DictOfFetchedTensorValues = Dict[KeyType, Dict[Text, TensorValue]]

MetricVariablesType = List[Any]


class ValueWithConfidenceInterval(
    NamedTuple('ValueWithConfidenceInterval', [
        ('value', float),
        ('lower_bound', float),
        ('upper_bound', float),
        ('unsampled_value', float),
    ])):
  """Represents a value with mean, upper, and lower bound."""

  def __new__(
      cls,
      value,
      lower_bound = None,
      upper_bound = None,
      unsampled_value = None,
  ):
    # Add bounds checking?
    return super(ValueWithConfidenceInterval, cls).__new__(
        cls, value, lower_bound, upper_bound, unsampled_value)


# AddMetricsCallback should have the following prototype:
#   def add_metrics_callback(features_dict, predictions_dict, labels_dict):
#
# It should create and return a metric_ops dictionary, such that
# metric_ops['metric_name'] = (value_op, update_op), just as in the Trainer.
#
# Note that features_dict, predictions_dict and labels_dict are not
# necessarily dictionaries - they might also be Tensors, depending on what the
# model's eval_input_receiver_fn returns.
AddMetricsCallbackType = Any

FeaturesPredictionsLabels = NamedTuple(
    'FeaturesPredictionsLabels', [('input_ref', int),
                                  ('features', DictOfFetchedTensorValues),
                                  ('predictions', DictOfFetchedTensorValues),
                                  ('labels', DictOfFetchedTensorValues)])

# Used in building the model diagnostics table, a MaterializedColumn is a value
# inside of Extracts that will be emitted to file. Note that for strings, the
# values are raw byte strings rather than unicode strings. This is by design, as
# features can have arbitrary bytes values.
MaterializedColumn = NamedTuple(
    'MaterializedColumn',
    [('name', Text),
     ('value', Union[List[bytes], List[int], List[float], bytes, int, float])])

# Extracts represent data extracted during pipeline processing. In order to
# provide a flexible API, these types are just dicts where the keys are defined
# (reserved for use) by different extractor implementations. For example, the
# PredictExtractor stores the data for the features, labels, and predictions
# under the keys "features", "labels", and "predictions".
Extracts = Dict[Text, Any]

# pylint: enable=invalid-name


def is_tensor(obj):
  return isinstance(obj, tf.Tensor) or isinstance(obj, tf.SparseTensor)


class EvalSharedModel(
    NamedTuple(
        'EvalSharedModel',
        [
            ('model_path', Text),
            ('add_metrics_callbacks',
             List[Callable]),  # List[AnyMetricsCallbackType]
            ('include_default_metrics', bool),
            ('example_weight_key', Text),
            ('shared_handle', shared.Shared),
            ('construct_fn', Callable)
        ])):
  # pyformat: disable
  """Shared model used during extraction and evaluation.

  Attributes:
    model_path: Path to EvalSavedModel (containing the saved_model.pb file).
    add_metrics_callbacks: Optional list of callbacks for adding additional
      metrics to the graph. The names of the metrics added by the callbacks
      should not conflict with existing metrics. See below for more details
      about what each callback should do. The callbacks are only used during
      evaluation.
    include_default_metrics: True to include the default metrics that are part
      of the saved model graph during evaluation.
    example_weight_key: The key of the example weight column. If None, weight
      will be 1 for each example.
    shared_handle: Optional handle to a shared.Shared object for sharing the
      in-memory model within / between stages.
    construct_fn: A callable which creates a construct function
      to set up the tensorflow graph. Callable takes a beam.metrics distribution
      to track graph construction time.

  More details on add_metrics_callbacks:

    Each add_metrics_callback should have the following prototype:
      def add_metrics_callback(features_dict, predictions_dict, labels_dict):

    Note that features_dict, predictions_dict and labels_dict are not
    necessarily dictionaries - they might also be Tensors, depending on what the
    model's eval_input_receiver_fn returns.

    It should create and return a metric_ops dictionary, such that
    metric_ops['metric_name'] = (value_op, update_op), just as in the Trainer.

    Short example:

    def add_metrics_callback(features_dict, predictions_dict, labels):
      metrics_ops = {}
      metric_ops['mean_label'] = tf.metrics.mean(labels)
      metric_ops['mean_probability'] = tf.metrics.mean(tf.slice(
        predictions_dict['probabilities'], [0, 1], [2, 1]))
      return metric_ops
  """
  # pyformat: enable

  def __new__(
      cls,
      model_path = None,
      add_metrics_callbacks = None,
      include_default_metrics = True,
      example_weight_key = None,
      shared_handle = None,
      construct_fn = None):
    if not add_metrics_callbacks:
      add_metrics_callbacks = []
    if not shared_handle:
      shared_handle = shared.Shared()
    return super(EvalSharedModel, cls).__new__(
        cls, model_path, add_metrics_callbacks, include_default_metrics,
        example_weight_key, shared_handle, construct_fn)
