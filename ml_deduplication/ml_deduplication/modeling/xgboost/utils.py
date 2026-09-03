import logging

import numpy as np
from sklearn.metrics import (
    classification_report,
    fbeta_score,
    precision_score,
    recall_score,
)

logger = logging.getLogger(__name__)


def select_best_threshold(
    y_pred_scores_dev: np.ndarray, y_dev: np.ndarray, min_recall: float = 0.6
) -> tuple[float, dict]:

    best_threshold = 0
    best_precision = 0

    best_fbeta = 0
    best_fbeta_threshold = 0
    y_pred_scores = y_pred_scores_dev[:, 1]
    for threshold in np.arange(0.1, 1, 0.05):
        y_pred_labels = y_pred_scores >= threshold

        precision = precision_score(y_dev, y_pred_labels)
        recall = recall_score(y_dev, y_pred_labels)
        fbeta = fbeta_score(y_dev, y_pred_labels, beta=0.3)

        if (precision > best_precision) and (recall >= min_recall):
            best_threshold = threshold
            best_precision = precision

        if fbeta > best_fbeta:
            best_fbeta = fbeta
            best_fbeta_threshold = threshold

    if best_precision > 0:
        y_pred_labels_at_best_threshold = y_pred_scores >= best_threshold
    else:
        logger.debug(
            "Using fbeta to get threshold as best precision do not reach min recall."
        )
        best_threshold = best_fbeta_threshold
        y_pred_labels_at_best_threshold = y_pred_scores >= best_threshold
    classification_report_at_best_thresold: dict = classification_report(
        y_dev, y_pred_labels_at_best_threshold, output_dict=True
    )  # type: ignore

    return best_threshold, classification_report_at_best_thresold
