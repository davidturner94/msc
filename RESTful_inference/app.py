from flask import Flask, jsonify, request, Markup
import torch
from time import perf_counter_ns, time
import tools.utils as utils
from tools.utils import get_top5
import torchvision.models as models
import torchvision.transforms as transforms
import torchsummary
from PIL import Image
from io import BytesIO


app = Flask(__name__)

net = models.resnet18(pretrained=True)
net.name = "resent18"
net.eval()
net.to(utils.DEVICE)
net_info = torchsummary.summary(net, (3, 224, 224))


@app.route("/")
def index():
    """
    :return: json response
    :rtype: json object
    """
    response = {
        "status": "All Good.",
        "device": utils.DEVICE.type,
        "current_model": net.name
    }
    return jsonify(response)


@app.route("/inference", methods=["POST"])
def inference():
    """
    Method for inference on a provided image

    This method takes a json request containing an image and the model to test
    and returns json data containing the predicted result and some meta data
    relating to inference time and confidence score.


    """
    # Convery bytes to image
    # print(request.files["files"])
    im = Image.open(BytesIO(request.files['files'].read()))
    # im.show()

    # image preprocessing: convert to tensor and add dimension to mimick batch
    im_tensor = transforms.ToTensor()(im)

    im_tensor = transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                     std=[0.229, 0.224, 0.225])(im_tensor)

    data = im_tensor.unsqueeze(0)
    data = data.to(utils.DEVICE)

    # # run inference
    perf_start = perf_counter_ns()

    # # inference here
    (top5_values, top5_indicies), raw = get_top5(net, data)

    perf_end = perf_counter_ns()

    # return results as a json
    return jsonify({
        "result": {
            "prediction_raw": raw[0].tolist(),
            "predicted_class": [top5_indicies[0][0].item()],
            "confidence": [top5_values[0][0].item()],
            "top5": [x.item() for x in top5_indicies[0]],
            "top5_confidence": [x.item() for x in top5_values[0]],
            "inference_time_ms": (perf_end-perf_start) / 10**6,
        },
        "meta": {
            "device": utils.DEVICE.type,
            "model": {
                "name": net.name,
                "size_in_MB": net_info['total_size'],
                "no_params": net_info['total_params'],
            },
            "time_now": perf_counter_ns(),  # This is to enable calculation of latency

        }
    })


@ app.route("/currentmodel")
def model():
    return jsonify(torchsummary.summary(net, (3, 224, 224)))


@app.route("/changemodel/<slug>")
def change_model(model):
    return(jsonify({"Error": "Not Yet Implimented."}))


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)