import vtk
import itertools

def rotation_array(actor_row_list, 
                   rotations = 3, 
                   rotation_axis = "azimuth", 
                   dimensions = [1000,1000],
                   background_color = [1,1,1], 
                   focuspoints = [], 
                   row_names = [],
                   zoomfactor = 1, 
                   transpose = False):
    '''
    Create an image where rows are a rotation series of images containing actors from each element in actor_row_list. 
    returns vtkImageData.
    In the future, I may allow passing a render window, from which settings (camera, lighting) can be copied to windows used for each row.
    '''
    #If there are no focuspoints, create an empty list of correct length that results in default camera focus position being used
    if len(focuspoints) != len(actor_row_list):
        if len(focuspoints = 0):
            focuspoints = None * len(actor_row_list)
        else:
            print('Parameters actor_row_list and focuspoints not of same length.')
            print('Rotation panel not constructed')  
#             break  
            
    if transpose:
            row_axis = 1
            column_axis = 0
    else:
            row_axis = 0
            column_axis = 1
            
    #contruct a row for each element in actor_set
    rows = []    
    for (actor_set, focuspoint, name) in itertools.zip_longest(actor_row_list, focuspoints, row_names):
        renWin = simple_vtkRenderWindow(actors = actor_set, 
                                        render_dimensions = dimensions,
                                        background_color = background_color,
                                        camera_focuspoint = focuspoint, 
                                        zoomfactor = zoomfactor, 
                                        display_window = False)
        images = rotation_series(render_window = renWin,
                                 rotations = rotations, 
                                 rotation_axis = rotation_axis, 
                                 append_ID = True,
                                 series_name = name)
        
        rows.append(concatenate_vtkImageData(vtkImageDataList = images, axis = row_axis))
        
        #properly delete vtk resources
        iren = renWin.GetInteractor()
        renWin.Finalize()
        iren.TerminateApp()
        del renWin, iren
    return concatenate_vtkImageData(vtkImageDataList = rows, axis = column_axis)

def concatenate_vtkImageData(vtkImageDataList, axis = 0):
    '''
    Combine vtkImageData objects along an axis
    
    Parameters
    ----------
    vtkImageDataList : list
        vtkImageData to be concatenated
    axis : int
        0,1, or 2
    '''
    appender = vtk.vtkImageAppend()
    appender.SetAppendAxis(axis)
    for i in vtkImageDataList:
        appender.AddInputData(i)
    appender.Update()
    return appender.GetOutput()

def rotation_series(render_window, 
                    rotations = 3, 
                    rotation_axis = "azimuth", 
                    append_ID = True, 
                    series_name = '',
                    label_background = [0,1,0],
                    label_font_size = 10,
                    label_color = [1,0,0], 
                    label_orientation = 'vertical'):
    '''
    Collect a series of images as a camera rotates around an object. 
    
    Parameters
    ----------
    renderWindow : vtk.vtkRenderWindow
        Window to manipulate and grab images from
    rotationAxis : str
        accepts azimuth or elevation
    rotationNumber : int
        number of images to generate
    '''
    iren = render_window.GetInteractor()
    if iren.GetInitialized() == 0:
        iren.Initialize()
    render_window.OffScreenRenderingOn()
    renderer = render_window.GetRenderers().GetFirstRenderer()    
    camera=renderer.GetActiveCamera() 

    images =[]
    
    if append_ID:
        text_actor = vtk.vtkCaptionActor2D()
        text_actor.SetAttachmentPoint((0.0,-0.15,0.0))#position relative to center of screen
        text_actor.SetPosition(0,0)#position relative to attachment point
        text_actor.SetCaption(str(series_name))
        text_actor.GetCaptionTextProperty().SetJustificationToLeft()
        text_actor.GetCaptionTextProperty().SetFontSize(24)
        text_actor.GetCaptionTextProperty().SetVerticalJustificationToCentered()
        text_actor.GetCaptionTextProperty().UseTightBoundingBoxOn()
# #         text_actor.GetTextActor().SetTextScaleModeToProp()
        text_actor.GetTextActor().SetTextScaleModeToViewport()#This seems to work best?
#         text_actor.GetTextActor().SetTextScaleModeToNone()
        text_actor.BorderOff()
        text_actor.GetCaptionTextProperty().SetVerticalJustificationToCentered()
        text_actor.GetCaptionTextProperty().SetOrientation(90)
            
        #build renderwindow
        size = render_window.GetSize()#I might make it so it is smaller in one dimension
        label_dimensions = []
        if label_orientation == 'vertical':
            label_dimensions = [int(0.1*size[0]), size[1]]
        else:
            label_dimensions = [size[0], int(0.1*size[1])]
        label_renWin =simple_vtkRenderWindow(actors = [text_actor],
                                             render_dimensions = label_dimensions,
                                             background_color = [0,0,1], 
                                             display_window = False)
        label_iren = label_renWin.GetInteractor()
        if label_iren.GetInitialized() == 0:
            label_iren.Initialize()
        label_renderer = label_renWin.GetRenderers().GetFirstRenderer()
        label_renWin.OffScreenRenderingOn()

        #grab and append image
        image_filter = vtk.vtkWindowToImageFilter()
        image_filter.SetInput(label_renWin)
        image_filter.Modified()
        image_filter.Update()
        images.append(image_filter.GetOutput())
        
        #clean up resources
        del image_filter
        label_renWin.Finalize()
        label_iren.TerminateApp()
        del label_renWin, label_iren

    #rotation images
    for x in range(rotations):
        image_filter = vtk.vtkWindowToImageFilter()
        image_filter.SetInput(render_window)
        image_filter.Modified()
        image_filter.Update()
        images.append(image_filter.GetOutput())
        if rotation_axis == 'azimuth':
            camera.Azimuth(360/rotations)
        elif rotation_axis == 'elevation':
            camera.Elevation(360/rotations)
        del image_filter
        
    return images

def label_series(labels, image_width, image_height, text_orientation = "vertical", background_color = [0,0,0]):
    '''not yet tested, might not work'''
    label_images = []
    for label in labels:
        text_actor = vtk.vtkCaptionActor2D()
        text_actor.SetAttachmentPoint((0.0,-0.15,0.0))#position relative to center of screen
        text_actor.SetPosition(0,0)#position relative to attachment point
        text_actor.SetCaption(str(label))
        text_actor.GetCaptionTextProperty().SetJustificationToLeft()
        text_actor.GetCaptionTextProperty().SetFontSize(24)
        text_actor.GetCaptionTextProperty().SetVerticalJustificationToCentered()
        text_actor.GetCaptionTextProperty().UseTightBoundingBoxOn()
        # #         text_actor.GetTextActor().SetTextScaleModeToProp()
        text_actor.GetTextActor().SetTextScaleModeToViewport()#This seems to work best?
        #         text_actor.GetTextActor().SetTextScaleModeToNone()
        text_actor.BorderOff()
        text_actor.GetCaptionTextProperty().SetVerticalJustificationToCentered()
        text_actor.GetCaptionTextProperty().SetOrientation(90)
            
        label_renWin =simple_vtkRenderWindow(actors = [text_actor],
                                                render_dimensions = [image_width, image_height],
                                                background_color = background_color, 
                                                display_window = False)
        label_iren = label_renWin.GetInteractor()
        if label_iren.GetInitialized() == 0:
            label_iren.Initialize()
        label_renderer = label_renWin.GetRenderers().GetFirstRenderer()
        label_renWin.OffScreenRenderingOn()

        #grab and append image
        image_filter = vtk.vtkWindowToImageFilter()
        image_filter.SetInput(label_renWin)
        image_filter.Modified()
        image_filter.Update()
        label_images.append(image_filter.GetOutput())

        #clean up resources
        del image_filter
        label_renWin.Finalize()
        label_iren.TerminateApp()
        del label_renWin, label_iren
    
    return label_images

def simple_vtkRenderWindow(actors = [], 
                           camera = None, 
                           background_color = [0,0,0], 
                           render_dimensions = [1000,1000], 
                           camera_focuspoint = [], 
                           zoomfactor = 1, 
                           interactor_style = 'trackball', 
                           display_window = False):

    '''
    Create a vtkRenderWindow, with option to display
    '''
    ren = vtk.vtkRenderer()
    ren.UseFXAAOn()#turns anti-aliasing on
    ren.SetBackground(background_color)
    if len(actors) > 0:
        for actor in actors:
            ren.AddActor(actor)
    ren.ResetCamera()
    
    if camera == None:
        camera = ren.GetActiveCamera()

    else:
        ren.SetActiveCamera(camera)
    
    if len(camera_focuspoint) != 0:  
        camera.SetFocalPoint(camera_focuspoint)    
    
    camera.Dolly(zoomfactor)
    ren.ResetCameraClippingRange()#must be called after moving with Dolly
    
    renWin = vtk.vtkRenderWindow()
    renWin.AddRenderer(ren)
#     render_dimensions = render_d
    renWin.SetSize(render_dimensions[0],render_dimensions[1])
    
    iren = vtk.vtkRenderWindowInteractor()
    iren.SetRenderWindow(renWin)
    if interactor_style == 'trackball':
        trackCamera = vtk.vtkInteractorStyleTrackballCamera()
        iren.SetInteractorStyle(trackCamera)
    iren.Render()
    if display_window:
        iren.Initialize()
        iren.Start()
    return renWin

