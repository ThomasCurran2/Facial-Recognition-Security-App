
# **Facial recognition security app**

Security application that allows users to protect their apps with facial recognition.

## **Description**

This project is a Python application that allows user's to sign in, manage what apps they want protected, and enable facial recognition to verify if
a user is allowed to open those protected apps. The facial recognition utilizes machine learning with a siamese neural network being used to 
calculate the differences between the user's webcam image and the verification images saved to the app. Created as an alternative to other
security apps that don't use biometric data. 

## **Table of Contents**

- [Installation](#installation)
- [Usage](#usage)
- [Features](#features)
- [Reasources](#reasources)
- [Known issues and future development](#known-issues-and-future-development)
- [License](#license)

## **Installation**

To install this project, follow these steps:

1. Clone the repository: **https://github.com/Thomas-Curran-Projects/Face-Security-App.git**
2. Install dependencies
3. Run the app.py file

## **Usage**

To use this app, follow these steps:

1. Open the project a code editor.
2. Modify the source code to fit your needs.
3. Run the app.py file.

Demo Video:

https://github.com/user-attachments/assets/fcd203d2-d295-4eb6-aec2-b32a5cd0a013

## **Features**

1. Sign in and Login page
<p align="center">
    <img src = "images/searchBar.PNG" width = 500>
  </p>
2. Saving face id images
<p align="center">
  <img src = "images/hints.PNG" width = 300> <img src = "images/resultScreen.PNG" width = 350>
  </p>
3. Security management
<p align="center">
  <img src = "images/toolTip.PNG" width = 700>
  </p>
4. Face verification
<p align="center">
  <img src = "images/popUp.PNG" width = 700>
 </p>

## **Reasources**

Here are some helpful links and videos:

- **[`Qt for Python documentation`](https://doc.qt.io/qtforpython-6/)**
- **[`Siamese neural network info`](https://www.cs.cmu.edu/~rsalakhu/papers/oneshot1.pdf)**
- **[`Siamese neural network setup`](https://www.youtube.com/watch?v=LKispFFQ5GU)**

## **Known issues and future development**

Issues:

1. Background processes of protected apps may prompt the user for verification while the monitor window is open.

Future development:

Development on bug fixes are on going and will be added as soon as possible. 

## **License**

Commercile is released under the MIT License. See the **[MIT licensing page](https://tlo.mit.edu/understand-ip/exploring-mit-open-source-license-comprehensive-guide)** for details.

## **Authors and Acknowledgment**

Created by **[Thomas Curran](https://github.com/ThomasCurran2)**.

## **Changelog**

- **0.1.0:** Initial release
