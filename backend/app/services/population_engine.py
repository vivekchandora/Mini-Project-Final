def annual_growth_rate(start,end,years):
    if start<=0 or end<0 or years<=0: raise ValueError("Invalid population or period")
    return (end/start)**(1/years)-1
def project(base,rate,years):
    if base<0 or years<0 or not -1<=rate<=1: raise ValueError("Invalid projection inputs")
    return round(base*(1+rate)**years)
